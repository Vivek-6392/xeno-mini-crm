"""Segments API — manage customer segments and preview rule sets."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.database import get_db
from app.models.customer import Customer
from app.models.segment import Segment
from app.schemas import CustomerOut, SegmentCreate, SegmentOut
from app.services.segment_engine import evaluate_segment, count_segment

router = APIRouter(prefix="/api/segments", tags=["segments"])


class RulesPreviewRequest(BaseModel):
    rules: Dict[str, Any]


@router.post("/preview", summary="Count customers matching rules (no save)")
def preview_rules(payload: RulesPreviewRequest, db: Session = Depends(get_db)):
    customers = evaluate_segment(db, payload.rules)
    sample = [
        {
            "id": c.id,
            "name": c.name,
            "city": c.city,
            "total_spent": round(c.total_spent, 2),
            "total_orders": c.total_orders,
        }
        for c in customers[:10]
    ]
    return {"matching_count": len(customers), "sample": sample}


@router.post("/", response_model=SegmentOut, status_code=201)
def create_segment(payload: SegmentCreate, db: Session = Depends(get_db)):
    count = count_segment(db, payload.rules)
    seg = Segment(
        name=payload.name,
        description=payload.description,
        rules=payload.rules,
        customer_count=count,
        created_by_ai=payload.created_by_ai,
    )
    db.add(seg)
    db.commit()
    db.refresh(seg)
    return seg


@router.get("/", response_model=List[SegmentOut])
def list_segments(db: Session = Depends(get_db)):
    return db.query(Segment).order_by(Segment.created_at.desc()).all()


@router.get("/{segment_id}", response_model=SegmentOut)
def get_segment(segment_id: str, db: Session = Depends(get_db)):
    seg = db.query(Segment).filter(Segment.id == segment_id).first()
    if not seg:
        raise HTTPException(404, "Segment not found")
    return seg


@router.get("/{segment_id}/customers", response_model=List[CustomerOut])
def get_segment_customers(segment_id: str, db: Session = Depends(get_db)):
    seg = db.query(Segment).filter(Segment.id == segment_id).first()
    if not seg:
        raise HTTPException(404, "Segment not found")
    return evaluate_segment(db, seg.rules)


@router.delete("/{segment_id}", status_code=204)
def delete_segment(segment_id: str, db: Session = Depends(get_db)):
    seg = db.query(Segment).filter(Segment.id == segment_id).first()
    if not seg:
        raise HTTPException(404, "Segment not found")
    db.delete(seg)
    db.commit()
