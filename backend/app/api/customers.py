"""Customers API — CRUD + CSV bulk import."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.models.order import Order
from app.schemas import CustomerCreate, CustomerOut

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/", response_model=List[CustomerOut])
def list_customers(
    skip: int = 0,
    limit: int = 50,
    city: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Customer)
    if city:
        q = q.filter(Customer.city == city)
    return q.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(404, "Customer not found")
    return c


@router.post("/", response_model=CustomerOut, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    if db.query(Customer).filter(Customer.email == payload.email).first():
        raise HTTPException(409, "Email already registered")
    c = Customer(**payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.post("/import/csv", summary="Bulk-import customers via CSV upload")
async def import_customers_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Expects a CSV with headers:
        name, email, phone, city
    Orders can be omitted; they can be imported separately.
    """
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

    created, skipped = 0, 0
    for row in reader:
        email = row.get("email", "").strip().lower()
        if not email:
            skipped += 1
            continue
        if db.query(Customer).filter(Customer.email == email).first():
            skipped += 1
            continue
        c = Customer(
            name=row.get("name", "Unknown").strip(),
            email=email,
            phone=row.get("phone", "").strip() or None,
            city=row.get("city", "").strip() or None,
        )
        db.add(c)
        created += 1

    db.commit()
    return {"created": created, "skipped": skipped}


@router.get("/stats/overview")
def customer_overview(db: Session = Depends(get_db)):
    from sqlalchemy import func

    total = db.query(Customer).count()
    row = db.query(
        func.coalesce(func.sum(Customer.total_spent), 0).label("revenue"),
        func.coalesce(func.avg(Customer.total_spent), 0).label("avg_ltv"),
        func.coalesce(func.avg(Customer.total_orders), 0).label("avg_orders"),
    ).first()

    cities = (
        db.query(Customer.city, func.count(Customer.id))
        .filter(Customer.city.isnot(None))
        .group_by(Customer.city)
        .order_by(func.count(Customer.id).desc())
        .limit(5)
        .all()
    )

    return {
        "total_customers": total,
        "total_revenue": round(float(row.revenue), 2),
        "avg_lifetime_value": round(float(row.avg_ltv), 2),
        "avg_orders_per_customer": round(float(row.avg_orders), 2),
        "top_cities": [{"city": c, "count": n} for c, n in cities],
    }
