"""
Segment Rule Engine
===================
Translates the JSON rules stored on a Segment into a SQLAlchemy query
against the customers table.

Supported fields
----------------
total_spent         | gte, lte, gt, lt, eq
total_orders        | gte, lte, gt, lt, eq
days_since_last_order | gte, lte  (computed from last_order_date)
created_within_days | lte        (customer age in days)
city                | in, not_in  (value must be a list)

All conditions in the `conditions` array are combined with the top-level
`operator` ("AND" or "OR").
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.customer import Customer


def evaluate_segment(db: Session, rules: Dict[str, Any]) -> List[Customer]:
    """Return Customer rows that match the given rules dict."""
    conditions = [
        _build_condition(c["field"], c["operator"], c["value"])
        for c in rules.get("conditions", [])
        if _build_condition(c["field"], c["operator"], c["value"]) is not None
    ]

    if not conditions:
        return db.query(Customer).all()

    combinator = and_ if rules.get("operator", "AND").upper() == "AND" else or_
    return db.query(Customer).filter(combinator(*conditions)).all()


def count_segment(db: Session, rules: Dict[str, Any]) -> int:
    """Cheap COUNT(*) without loading full ORM objects."""
    conditions = [
        _build_condition(c["field"], c["operator"], c["value"])
        for c in rules.get("conditions", [])
        if _build_condition(c["field"], c["operator"], c["value"]) is not None
    ]
    if not conditions:
        return db.query(Customer).count()

    combinator = and_ if rules.get("operator", "AND").upper() == "AND" else or_
    return db.query(Customer).filter(combinator(*conditions)).count()


def _build_condition(field: str, op: str, value: Any):
    """Map a single {field, operator, value} dict to a SQLAlchemy clause."""
    now = datetime.utcnow()

    # ── Computed date fields ──────────────────────────────────────────────
    if field == "days_since_last_order":
        if op == "lte":   # active within N days
            return Customer.last_order_date >= (now - timedelta(days=value))
        if op == "gte":   # lapsed for at least N days
            return Customer.last_order_date <= (now - timedelta(days=value))
        return None

    if field == "created_within_days":
        return Customer.created_at >= (now - timedelta(days=value))

    # ── Direct column fields ──────────────────────────────────────────────
    col_map = {
        "total_spent": Customer.total_spent,
        "total_orders": Customer.total_orders,
        "city": Customer.city,
    }
    col = col_map.get(field)
    if col is None:
        return None

    op_map = {
        "gte": col >= value,
        "lte": col <= value,
        "gt": col > value,
        "lt": col < value,
        "eq": col == value,
        "in": col.in_(value if isinstance(value, list) else [value]),
        "not_in": col.notin_(value if isinstance(value, list) else [value]),
    }
    return op_map.get(op)
