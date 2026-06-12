"""
Channel Simulator
=================
Simulates real-world message delivery and engagement events.

For each communication we fire a sequence of events at randomised intervals,
mimicking the asynchronous, out-of-order nature of real channel delivery.

Delivery funnel by channel:
┌─────────────┬──────────┬──────────┬──────────┬──────────┬────────────┐
│ Channel     │ Delivery │ Open/Read│ Clicked  │Converted │Failure rate│
├─────────────┼──────────┼──────────┼──────────┼──────────┼────────────┤
│ WhatsApp    │   90 %   │   75 %   │   20 %   │   10 %   │   10 %     │
│ SMS         │   95 %   │   45 %   │    8 %   │    5 %   │    5 %     │
│ Email       │   85 %   │   35 %   │   12 %   │    8 %   │   15 %     │
│ RCS         │   80 %   │   55 %   │   18 %   │   12 %   │   20 %     │
└─────────────┴──────────┴──────────┴──────────┴──────────┴────────────┘

Timing (seconds after launch):
  sent:      0 – 2
  delivered: 1 – 5
  open/read: 5 – 60
  clicked:  10 – 120
  converted:30 – 180
"""
from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

# ── Channel probabilities ────────────────────────────────────────────────────

CHANNEL_PROBS: Dict[str, Dict[str, float]] = {
    "whatsapp": {"delivery": 0.90, "engage": 0.75, "click": 0.20, "convert": 0.10, "failure": 0.10},
    "sms":      {"delivery": 0.95, "engage": 0.45, "click": 0.08, "convert": 0.05, "failure": 0.05},
    "email":    {"delivery": 0.85, "engage": 0.35, "click": 0.12, "convert": 0.08, "failure": 0.15},
    "rcs":      {"delivery": 0.80, "engage": 0.55, "click": 0.18, "convert": 0.12, "failure": 0.20},
}

# "open" for email/rcs, "read" for whatsapp/sms
ENGAGE_EVENT = {
    "whatsapp": "read",
    "sms":      "read",
    "email":    "opened",
    "rcs":      "opened",
}


async def _post_event(callback_url: str, communication_id: str, event: str, delay: float):
    """Wait `delay` seconds then POST a receipt event to the CRM."""
    await asyncio.sleep(delay)
    payload = {
        "communication_id": communication_id,
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(callback_url, json=payload)
            resp.raise_for_status()
            logger.debug("✓ %s → %s", event, communication_id[:8])
    except Exception as exc:
        logger.warning("Failed to post %s for %s: %s", event, communication_id[:8], exc)


async def simulate_one(
    comm: Dict[str, Any],
    channel: str,
    callback_url: str,
) -> None:
    """Run the full event sequence for a single communication."""
    probs = CHANNEL_PROBS.get(channel, CHANNEL_PROBS["sms"])
    comm_id = comm["id"]

    tasks = []

    # 1. sent — always fires quickly
    tasks.append(_post_event(callback_url, comm_id, "sent", random.uniform(0, 2)))

    # 2. delivered or failed
    if random.random() < probs["delivery"]:
        tasks.append(_post_event(callback_url, comm_id, "delivered", random.uniform(1, 5)))

        # 3. engage (read / opened)
        if random.random() < probs["engage"]:
            engage_event = ENGAGE_EVENT[channel]
            tasks.append(_post_event(callback_url, comm_id, engage_event, random.uniform(5, 60)))

            # 4. clicked
            if random.random() < probs["click"]:
                tasks.append(_post_event(callback_url, comm_id, "clicked", random.uniform(10, 120)))

                # 5. converted
                if random.random() < probs["convert"]:
                    tasks.append(
                        _post_event(callback_url, comm_id, "converted", random.uniform(30, 180))
                    )
    else:
        # failure event
        tasks.append(_post_event(callback_url, comm_id, "failed", random.uniform(2, 10)))

    await asyncio.gather(*tasks)


async def simulate_campaign(
    campaign_id: str,
    channel: str,
    communications: List[Dict[str, Any]],
    callback_url: str,
) -> None:
    """
    Simulates delivery for an entire campaign.
    Each communication is processed concurrently (but independently).
    We add a small per-message jitter to avoid thundering-herd on the CRM.
    """
    logger.info(
        "Simulating %d messages for campaign %s via %s",
        len(communications),
        campaign_id[:8],
        channel,
    )

    # Stagger start to avoid hammering the callback URL with a burst
    semaphore = asyncio.Semaphore(20)  # max 20 concurrent simulations

    async def _run_with_limit(comm: Dict[str, Any]):
        jitter = random.uniform(0, 3)
        await asyncio.sleep(jitter)
        async with semaphore:
            await simulate_one(comm, channel, callback_url)

    await asyncio.gather(*[_run_with_limit(c) for c in communications])
    logger.info("Simulation complete for campaign %s", campaign_id[:8])
