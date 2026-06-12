"""
Channel Client
==============
Sends campaign communication batches to the stub channel service.
Uses httpx async client so it doesn't block the event loop.
The channel service will call back asynchronously to POST /api/receipts/.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def dispatch_to_channel(
    campaign_id: str,
    channel: str,
    communications: List[Dict[str, Any]],
) -> bool:
    """
    Fire campaign batch to the channel service.
    Returns True on success (202 Accepted from channel service).

    Failure is non-fatal: the campaign row is already created in the DB.
    We log the error and let the campaign sit in 'running' state.
    """
    payload = {
        "campaign_id": campaign_id,
        "channel": channel,
        "crm_callback_url": f"{settings.CRM_CALLBACK_URL}/api/receipts/",
        "communications": communications,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.CHANNEL_SERVICE_URL}/send",
                json=payload,
            )
            resp.raise_for_status()
            logger.info(
                "Channel service accepted campaign %s (%d messages)",
                campaign_id,
                len(communications),
            )
            return True
    except Exception as exc:
        logger.error(
            "Failed to dispatch campaign %s to channel service: %s",
            campaign_id,
            exc,
        )
        return False
