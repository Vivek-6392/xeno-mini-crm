import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Communication(Base):
    """
    One Communication = one message sent to one Customer as part of a Campaign.

    Status lifecycle (not all events fire for every channel):
        queued → sent → delivered → opened/read → clicked → converted
                      └→ failed
    """

    __tablename__ = "communications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False, index=True)

    channel = Column(String, nullable=False)
    message = Column(Text, nullable=False)  # personalised message text

    # Current status — last event received from channel service
    status = Column(String, default="queued", index=True)

    # Event timestamps (null until that event fires)
    queued_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    converted_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    campaign = relationship("Campaign", back_populates="communications")
    customer = relationship("Customer", back_populates="communications")
