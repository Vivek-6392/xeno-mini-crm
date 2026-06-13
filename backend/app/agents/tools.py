"""
Agent Tools
===========
Each tool wraps a CRM operation the AI agent can perform.
Tools run synchronously (the agent graph is invoked via asyncio.to_thread).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

import requests
from langchain_core.tools import tool

from app.config import settings
from app.database import SessionLocal
from app.models.campaign import Campaign
from app.models.communication import Communication
from app.models.customer import Customer
from app.models.segment import Segment
from app.services.segment_engine import evaluate_segment

logger = logging.getLogger(__name__)


def _db():
    return SessionLocal()


# ── 1. Customer overview ──────────────────────────────────────────────────────

@tool
def get_customer_stats(query: str = "") -> str:
    """
    Return high-level CRM stats: total customers, revenue, average spend,
    order frequency, and city distribution.
    Call this first to understand the customer base.
    """
    from sqlalchemy import func

    db = _db()
    try:
        total = db.query(Customer).count()
        row = db.query(
            func.coalesce(func.avg(Customer.total_spent), 0).label("avg_spent"),
            func.coalesce(func.avg(Customer.total_orders), 0).label("avg_orders"),
            func.coalesce(func.sum(Customer.total_spent), 0).label("revenue"),
        ).first()

        cities = (
            db.query(Customer.city, func.count(Customer.id))
            .filter(Customer.city.isnot(None))
            .group_by(Customer.city)
            .order_by(func.count(Customer.id).desc())
            .limit(10)
            .all()
        )

        return json.dumps({
            "total_customers": total,
            "total_revenue": round(float(row.revenue), 2),
            "avg_lifetime_value": round(float(row.avg_spent), 2),
            "avg_orders_per_customer": round(float(row.avg_orders), 2),
            "top_cities": {c: n for c, n in cities},
        })
    finally:
        db.close()


# ── 2. Segment preview ────────────────────────────────────────────────────────

@tool
def preview_segment(rules: dict) -> str:
    """
    Preview customers matching segment rules.
    """

    db = _db()

    try:
        customers = evaluate_segment(db, rules)

        sample = [
            {
                "name": c.name,
                "city": c.city,
                "total_spent": round(c.total_spent, 2),
                "total_orders": c.total_orders,
            }
            for c in customers[:5]
        ]

        return json.dumps({
            "matching_count": len(customers),
            "sample_customers": sample,
        })

    except Exception as e:
        return json.dumps({"error": str(e)})

    finally:
        db.close()


# ── 3. Create segment ─────────────────────────────────────────────────────────

@tool
def create_segment(
    name: str,
    description: str,
    rules: dict,
) -> str:
    """
    Create and save a segment.
    """

    db = _db()

    try:
        customers = evaluate_segment(db, rules)

        seg = Segment(
            name=name,
            description=description,
            rules=rules,
            customer_count=len(customers),
            created_by_ai=True,
        )

        db.add(seg)
        db.commit()
        db.refresh(seg)

        return json.dumps({
            "segment_id": seg.id,
            "name": seg.name,
            "customer_count": len(customers),
            "message": f"Segment '{name}' created successfully.",
        })

    except Exception as e:
        db.rollback()
        return json.dumps({
            "error": str(e)
        })

    finally:
        db.close()

# ── 4. List segments ──────────────────────────────────────────────────────────

@tool
def list_segments(query: str = "") -> str:
    """List the 10 most recent segments saved in the CRM."""
    db = _db()
    try:
        segs = db.query(Segment).order_by(Segment.created_at.desc()).limit(10).all()
        return json.dumps([
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "customer_count": s.customer_count,
                "created_at": s.created_at.isoformat(),
            }
            for s in segs
        ])
    finally:
        db.close()


# ── 5. Launch campaign ────────────────────────────────────────────────────────

@tool
def launch_campaign(
    campaign_name: str,
    segment_id: str,
    channel: str,
    message_template: str,
) -> str:
    """
    Create a Campaign, build per-recipient Communication rows, and fire the
    batch to the channel service.  The channel service will send delivery
    event callbacks back to the CRM asynchronously.

    campaign_name    - e.g. "Win-Back June 2025"
    segment_id       - from create_segment or list_segments
    channel          - one of: whatsapp | sms | email | rcs
    message_template - personalised text; use {name} as a placeholder
                       e.g. "Hi {name}, we miss you! Here's 20% off …"

    Always confirm details with the marketer before calling this tool.
    """
    db = _db()
    try:
        seg = db.query(Segment).filter(Segment.id == segment_id).first()
        if not seg:
            return json.dumps({"error": f"Segment '{segment_id}' not found."})

        campaign = Campaign(
            name=campaign_name,
            segment_id=segment_id,
            channel=channel,
            message_template=message_template,
            status="running",
            launched_at=datetime.utcnow(),
        )
        db.add(campaign)
        db.flush()  # get campaign.id before committing

        customers = evaluate_segment(db, seg.rules)
        campaign.total_sent = len(customers)

        channel_payload = []
        for c in customers:
            msg = message_template.replace("{name}", c.name)
            comm = Communication(
                campaign_id=campaign.id,
                customer_id=c.id,
                channel=channel,
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

        # Fire to channel service (synchronous in the tool; the channel service
        # responds immediately and processes the simulation in the background)
        try:
            requests.post(
                f"{settings.CHANNEL_SERVICE_URL}/send",
                json={
                    "campaign_id": campaign.id,
                    "channel": channel,
                    "crm_callback_url": f"{settings.CRM_CALLBACK_URL}/api/receipts/",
                    "communications": channel_payload,
                },
                timeout=10,
            )
        except Exception as exc:
            logger.warning("Channel service unreachable: %s", exc)

        return json.dumps({
            "campaign_id": campaign.id,
            "name": campaign_name,
            "segment": seg.name,
            "channel": channel,
            "total_recipients": len(customers),
            "status": "running",
            "message": (
                f"🚀 Campaign '{campaign_name}' launched to {len(customers)} customers "
                f"via {channel.upper()}. Delivery events will arrive shortly."
            ),
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"error": str(e)})
    finally:
        db.close()


# ── 6. Campaign analytics ─────────────────────────────────────────────────────

@tool
def get_campaign_analytics(campaign_id: str) -> str:
    """
    Return delivery and engagement stats for a specific campaign.
    Pass either a campaign_id or use list_campaigns first.
    """
    db = _db()
    try:
        c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not c:
            return json.dumps({"error": "Campaign not found"})

        t = c.total_sent or 1  # avoid division by zero

        def pct(n: int) -> str:
            return f"{round(n / t * 100, 1)}%"

        return json.dumps({
            "id": c.id,
            "name": c.name,
            "channel": c.channel,
            "status": c.status,
            "sent": c.total_sent,
            "delivered": c.total_delivered,
            "failed": c.total_failed,
            "opened": c.total_opened,
            "read": c.total_read,
            "clicked": c.total_clicked,
            "converted": c.total_converted,
            "delivery_rate": pct(c.total_delivered),
            "engagement_rate": pct(c.total_opened + c.total_read),
            "click_rate": pct(c.total_clicked),
            "conversion_rate": pct(c.total_converted),
        })
    finally:
        db.close()


# ── 7. List campaigns ─────────────────────────────────────────────────────────

@tool
def list_campaigns(query: str = "") -> str:
    """List the 10 most recent campaigns with summary stats."""
    db = _db()
    try:
        camps = db.query(Campaign).order_by(Campaign.created_at.desc()).limit(10).all()
        return json.dumps([
            {
                "id": c.id,
                "name": c.name,
                "channel": c.channel,
                "status": c.status,
                "sent": c.total_sent,
                "delivered": c.total_delivered,
                "clicked": c.total_clicked,
                "converted": c.total_converted,
                "launched_at": c.launched_at.isoformat() if c.launched_at else None,
            }
            for c in camps
        ])
    finally:
        db.close()


# Exported list used to bind tools to the graph
ALL_TOOLS = [
    get_customer_stats,
    preview_segment,
    create_segment,
    list_segments,
    launch_campaign,
    get_campaign_analytics,
    list_campaigns,
]
