"""
Receipts API
============
The channel service POSTs delivery / engagement events here.
Each event advances the Communication status and increments the
parent Campaign's aggregate counters.

This is the callback handler in the two-service delivery loop.
"""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.campaign import Campaign
from app.models.communication import Communication
from app.schemas import ReceiptEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/receipts", tags=["receipts"])

# Maps event name → (Communication timestamp field, Campaign counter field)
EVENT_MAP = {
    "sent":      ("sent_at",      None),
    "delivered": ("delivered_at", "total_delivered"),
    "failed":    ("failed_at",    "total_failed"),
    "opened":    ("opened_at",    "total_opened"),
    "read":      ("read_at",      "total_read"),
    "clicked":   ("clicked_at",   "total_clicked"),
    "converted": ("converted_at", "total_converted"),
}

# Status priority — only advance forward, never regress
STATUS_ORDER = ["queued", "sent", "delivered", "opened", "read", "clicked", "converted", "failed"]


@router.post("/", status_code=204)
def ingest_receipt(event: ReceiptEvent, db: Session = Depends(get_db)):
    """
    Idempotent: if the same event arrives twice we silently skip it.
    """
    comm = (
        db.query(Communication)
        .filter(Communication.id == event.communication_id)
        .first()
    )
    if not comm:
        logger.warning("Receipt for unknown communication %s", event.communication_id)
        raise HTTPException(404, "Communication not found")

    ts_field, counter_field = EVENT_MAP.get(event.event, (None, None))
    if ts_field is None:
        logger.warning("Unknown event type: %s", event.event)
        raise HTTPException(400, f"Unknown event '{event.event}'")

    # Idempotency: skip if this timestamp is already set
    if getattr(comm, ts_field) is not None:
        return  # already processed

    setattr(comm, ts_field, event.timestamp)

    # Advance status only forward
    curr_idx = STATUS_ORDER.index(comm.status) if comm.status in STATUS_ORDER else 0
    new_idx = STATUS_ORDER.index(event.event) if event.event in STATUS_ORDER else 0
    if new_idx > curr_idx:
        comm.status = event.event

    # Increment campaign counter
    if counter_field:
        campaign = db.query(Campaign).filter(Campaign.id == comm.campaign_id).first()
        if campaign:
            setattr(campaign, counter_field, getattr(campaign, counter_field, 0) + 1)

            # Auto-complete campaign when all messages are terminal
            _maybe_complete_campaign(campaign, db)

    db.commit()
    logger.debug("Receipt processed: %s → %s", event.communication_id, event.event)


def _maybe_complete_campaign(campaign: Campaign, db: Session):
    """Mark campaign completed if every communication has a terminal status."""
    terminal = campaign.total_delivered + campaign.total_failed
    if terminal >= campaign.total_sent > 0:
        campaign.status = "completed"
        campaign.completed_at = datetime.utcnow()
