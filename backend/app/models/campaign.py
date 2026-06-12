import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Campaign(Base):
    """
    A campaign targets one Segment over one Channel.
    Aggregate delivery/engagement counters are incremented by the receipt handler
    as callbacks arrive from the channel service.
    """

    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    segment_id = Column(String, ForeignKey("segments.id"), nullable=False)
    channel = Column(String, nullable=False)  # whatsapp | sms | email | rcs
    message_template = Column(Text, nullable=False)

    # Lifecycle: draft → running → completed | failed
    status = Column(String, default="draft", index=True)

    # ── Delivery counters (incremented by receipt callbacks) ──────────────
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)   # email / rcs
    total_read = Column(Integer, default=0)      # whatsapp / sms
    total_clicked = Column(Integer, default=0)
    total_converted = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    launched_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    segment = relationship("Segment")
    communications = relationship(
        "Communication", back_populates="campaign", cascade="all, delete-orphan"
    )
