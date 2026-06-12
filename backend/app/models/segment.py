import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String

from app.database import Base


class Segment(Base):
    """
    Stores a named audience with JSON rules that the segment engine evaluates
    against the customers table at query time.

    Rules schema:
    {
        "operator": "AND" | "OR",
        "conditions": [
            {"field": "total_spent",          "operator": "gte",         "value": 5000},
            {"field": "total_orders",         "operator": "gte",         "value": 3},
            {"field": "days_since_last_order","operator": "lte",         "value": 30},
            {"field": "city",                 "operator": "in",          "value": ["Mumbai"]},
            {"field": "created_within_days",  "operator": "lte",         "value": 60}
        ]
    }
    """

    __tablename__ = "segments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, default="")
    rules = Column(JSON, nullable=False)

    # Cached count — refreshed each time the segment is previewed or saved
    customer_count = Column(Integer, default=0)

    created_by_ai = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
