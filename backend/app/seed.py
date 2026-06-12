"""
Seed Script — Coffee Chain Demo Data
=====================================
Creates 100 realistic customers and their order history.
Designed to produce interesting, explorable segments:

  • High-value loyalists  (total_spent > 8000, orders > 10)
  • Active regulars       (orders 4-10, last 30 days)
  • Lapsed customers      (no order in 60+ days)
  • New joiners           (created in last 30 days)
  • City clusters         (Mumbai, Delhi, Bangalore, Chennai, Pune)

Run:  python -m app.seed
"""
from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.customer import Customer
from app.models.order import Order

fake = Faker("en_IN")
random.seed(42)

CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Pune"]
CITY_WEIGHTS = [0.30, 0.25, 0.20, 0.15, 0.10]

MENU = [
    ("Espresso", 80),
    ("Cappuccino", 150),
    ("Latte", 160),
    ("Cold Brew", 180),
    ("Matcha Latte", 200),
    ("Croissant", 120),
    ("Blueberry Muffin", 90),
    ("Avocado Toast", 250),
    ("Club Sandwich", 280),
    ("Signature Blend (250g)", 650),
]

# Customer archetypes and their share of the 100 total
ARCHETYPES = {
    "high_value":  20,   # ₹8k+ total, 10+ orders
    "regular":     35,   # ₹2k–8k, 4–10 orders, last order < 30 days
    "lapsed":      25,   # last order 60–120 days ago
    "new":         15,   # joined last 30 days, 1–3 orders
    "one_time":     5,   # exactly 1 order ever
}


def _random_items(n: int = 2):
    selection = random.choices(MENU, k=n)
    return [{"name": item, "qty": random.randint(1, 3), "price": price} for item, price in selection]


def _make_orders(customer_id: str, archetype: str) -> list[Order]:
    now = datetime.utcnow()
    orders = []

    if archetype == "high_value":
        n = random.randint(10, 20)
        latest = now - timedelta(days=random.randint(1, 20))
    elif archetype == "regular":
        n = random.randint(4, 10)
        latest = now - timedelta(days=random.randint(1, 29))
    elif archetype == "lapsed":
        n = random.randint(3, 8)
        latest = now - timedelta(days=random.randint(60, 120))
    elif archetype == "new":
        n = random.randint(1, 3)
        latest = now - timedelta(days=random.randint(0, 20))
    else:  # one_time
        n = 1
        latest = now - timedelta(days=random.randint(10, 90))

    for i in range(n):
        order_date = latest - timedelta(days=i * random.randint(5, 20))
        items = _random_items(random.randint(1, 4))
        amount = round(sum(it["qty"] * it["price"] for it in items), 2)
        orders.append(
            Order(
                customer_id=customer_id,
                amount=amount,
                items=items,
                channel=random.choice(["online", "store", "online", "online"]),
                created_at=order_date,
            )
        )

    return orders


def seed():
    db = SessionLocal()
    existing = db.query(Customer).count()
    if existing >= 10:
        print(f"[seed] DB already has {existing} customers — skipping seed.")
        db.close()
        return

    print("[seed] Creating demo customers and orders …")
    created_customers = 0

    for archetype, count in ARCHETYPES.items():
        for _ in range(count):
            city = random.choices(CITIES, CITY_WEIGHTS)[0]
            joined = datetime.utcnow() - timedelta(days=random.randint(
                5 if archetype == "new" else 90, 365
            ))

            email = fake.unique.email()
            customer = Customer(
                name=fake.name(),
                email=email,
                phone=fake.phone_number()[:15],
                city=city,
                created_at=joined,
            )
            db.add(customer)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                continue

            orders = _make_orders(customer.id, archetype)
            for o in orders:
                db.add(o)
                customer.total_orders += 1
                customer.total_spent += o.amount

            if orders:
                customer.last_order_date = max(o.created_at for o in orders)

            created_customers += 1

    db.commit()
    db.close()
    print(f"[seed] ✅ Created {created_customers} customers with orders.")


if __name__ == "__main__":
    seed()
