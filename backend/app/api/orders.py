"""Orders API — create orders and keep customer aggregates in sync."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.models.order import Order
from app.schemas import OrderCreate, OrderOut

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/", response_model=OrderOut, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(404, "Customer not found")

    order = Order(**payload.model_dump())
    db.add(order)

    # Keep denormalised aggregates on customer up-to-date
    customer.total_orders += 1
    customer.total_spent += payload.amount
    if not customer.last_order_date or order.created_at > customer.last_order_date:
        customer.last_order_date = order.created_at

    db.commit()
    db.refresh(order)
    return order


@router.get("/customer/{customer_id}", response_model=List[OrderOut])
def get_customer_orders(customer_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Order)
        .filter(Order.customer_id == customer_id)
        .order_by(Order.created_at.desc())
        .all()
    )
