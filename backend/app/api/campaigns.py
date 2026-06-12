"""Campaigns API — create, launch and query campaign performance."""
from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.campaign import Campaign
from app.models.communication import Communication
from app.models.segment import Segment
from app.schemas import CampaignCreate, CampaignOut, CommunicationOut
from app.services.channel_client import dispatch_to_channel
from app.services.segment_engine import evaluate_segment

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.post("/", response_model=CampaignOut, status_code=201)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    seg = db.query(Segment).filter(Segment.id == payload.segment_id).first()
    if not seg:
        raise HTTPException(404, "Segment not found")

    campaign = Campaign(**payload.model_dump(), status="draft")
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/launch", response_model=CampaignOut)
async def launch_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Transitions a draft campaign to 'running', creates Communication rows for
    every customer in the segment, and fires the batch to the channel service.
    The channel service will POST delivery events back to /api/receipts/.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if campaign.status != "draft":
        raise HTTPException(400, f"Campaign is already '{campaign.status}'")

    seg = db.query(Segment).filter(Segment.id == campaign.segment_id).first()
    customers = evaluate_segment(db, seg.rules)

    campaign.status = "running"
    campaign.launched_at = datetime.utcnow()
    campaign.total_sent = len(customers)

    channel_payload = []
    for c in customers:
        msg = campaign.message_template.replace("{name}", c.name)
        comm = Communication(
            campaign_id=campaign.id,
            customer_id=c.id,
            channel=campaign.channel,
            message=msg,
            status="queued",
        )
        db.add(comm)
        channel_payload.append({
            "id": comm.id,
            "customer_name": c.name,
            "phone": c.phone or "",
            "email": c.email,
            "message": msg,
        })

    db.commit()
    db.refresh(campaign)

    background_tasks.add_task(
        dispatch_to_channel, campaign.id, campaign.channel, channel_payload
    )

    return campaign


@router.get("/", response_model=List[CampaignOut])
def list_campaigns(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return (
        db.query(Campaign)
        .order_by(Campaign.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/stats/overview")
def campaigns_overview(db: Session = Depends(get_db)):
    from sqlalchemy import func

    total = db.query(Campaign).count()
    running = db.query(Campaign).filter(Campaign.status == "running").count()
    completed = db.query(Campaign).filter(Campaign.status == "completed").count()

    row = db.query(
        func.coalesce(func.sum(Campaign.total_sent), 0).label("sent"),
        func.coalesce(func.sum(Campaign.total_delivered), 0).label("delivered"),
        func.coalesce(func.sum(Campaign.total_clicked), 0).label("clicked"),
        func.coalesce(func.sum(Campaign.total_converted), 0).label("converted"),
    ).first()

    return {
        "total": total,
        "running": running,
        "completed": completed,
        "all_time_sent": int(row.sent),
        "all_time_delivered": int(row.delivered),
        "all_time_clicked": int(row.clicked),
        "all_time_converted": int(row.converted),
    }


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(404, "Campaign not found")
    return c


@router.get("/{campaign_id}/communications", response_model=List[CommunicationOut])
def get_campaign_communications(
    campaign_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return (
        db.query(Communication)
        .filter(Communication.campaign_id == campaign_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
