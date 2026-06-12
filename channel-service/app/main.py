"""
Channel Service (Stub)
======================
Receives campaign batches from the CRM, immediately acknowledges them,
then simulates delivery/engagement events asynchronously and fires
callbacks back to the CRM receipt endpoint.

This two-service, callback-driven design mirrors real messaging providers
(Twilio, Gupshup, etc.) — the CRM never waits for delivery; it just
listens for events.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.simulator import simulate_campaign

app = FastAPI(
    title="Xeno Channel Service (Stub)",
    description="Simulates WhatsApp / SMS / Email / RCS delivery and fires callbacks to the CRM.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CRM_CALLBACK_URL = os.getenv("CRM_CALLBACK_URL", "http://localhost:8000")


# ── Request / Response models ─────────────────────────────────────────────────

class CommunicationItem(BaseModel):
    id: str
    customer_name: str
    phone: str = ""
    email: str = ""
    message: str


class SendPayload(BaseModel):
    campaign_id: str
    channel: str                        # whatsapp | sms | email | rcs
    crm_callback_url: str               # where to POST delivery events
    communications: List[CommunicationItem]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/send", status_code=202)
async def send_messages(payload: SendPayload, background_tasks: BackgroundTasks):
    """
    Accept a campaign batch.
    Responds immediately (202 Accepted) and kicks off simulation in the background.
    The simulation will POST delivery/engagement events back to `crm_callback_url`.
    """
    background_tasks.add_task(
        simulate_campaign,
        payload.campaign_id,
        payload.channel,
        [c.model_dump() for c in payload.communications],
        payload.crm_callback_url,
    )
    return {
        "status": "accepted",
        "campaign_id": payload.campaign_id,
        "channel": payload.channel,
        "queued": len(payload.communications),
        "message": f"Simulating {len(payload.communications)} messages via {payload.channel}.",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "xeno-channel-service"}
