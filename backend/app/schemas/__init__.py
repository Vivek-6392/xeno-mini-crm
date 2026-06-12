from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr


# ── Customer ──────────────────────────────────────────────────────────────────

class CustomerCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    city: Optional[str] = None


class CustomerOut(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    city: Optional[str]
    total_orders: int
    total_spent: float
    last_order_date: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Order ─────────────────────────────────────────────────────────────────────

class OrderCreate(BaseModel):
    customer_id: str
    amount: float
    items: List[Dict[str, Any]] = []
    channel: str = "online"


class OrderOut(BaseModel):
    id: str
    customer_id: str
    amount: float
    items: List[Dict[str, Any]]
    channel: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Segment ───────────────────────────────────────────────────────────────────

class SegmentCreate(BaseModel):
    name: str
    description: str = ""
    rules: Dict[str, Any]
    created_by_ai: bool = False


class SegmentOut(BaseModel):
    id: str
    name: str
    description: str
    rules: Dict[str, Any]
    customer_count: int
    created_by_ai: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Campaign ──────────────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    segment_id: str
    channel: str
    message_template: str


class CampaignOut(BaseModel):
    id: str
    name: str
    segment_id: str
    channel: str
    message_template: str
    status: str
    total_sent: int
    total_delivered: int
    total_failed: int
    total_opened: int
    total_read: int
    total_clicked: int
    total_converted: int
    created_at: datetime
    launched_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ── Communication ─────────────────────────────────────────────────────────────

class CommunicationOut(BaseModel):
    id: str
    campaign_id: str
    customer_id: str
    channel: str
    message: str
    status: str
    queued_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    read_at: Optional[datetime]
    clicked_at: Optional[datetime]
    converted_at: Optional[datetime]
    failed_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ── Receipt (from Channel Service) ───────────────────────────────────────────

class ReceiptEvent(BaseModel):
    communication_id: str
    event: str   # sent | delivered | failed | opened | read | clicked | converted
    timestamp: datetime


# ── Agent ─────────────────────────────────────────────────────────────────────

class AgentMessage(BaseModel):
    role: str   # user | assistant | tool
    content: str


class AgentChatRequest(BaseModel):
    message: str
    history: List[AgentMessage] = []
