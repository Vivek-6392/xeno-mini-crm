"""
Xeno Mini CRM — FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    agent_router,
    campaigns_router,
    customers_router,
    orders_router,
    receipts_router,
    segments_router,
)
from app.database import Base, engine

# Create all tables (safe to call multiple times — uses CREATE IF NOT EXISTS)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Xeno Mini CRM",
    description=(
        "An AI-native CRM for reaching shoppers. "
        "Chat with the Copilot, build segments, launch campaigns, and track results."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
for r in [
    customers_router,
    orders_router,
    segments_router,
    campaigns_router,
    receipts_router,
    agent_router,
]:
    app.include_router(r)


@app.get("/health")
def health():
    return {"status": "ok", "service": "xeno-crm-backend"}
