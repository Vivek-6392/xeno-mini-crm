from app.api.customers import router as customers_router
from app.api.orders import router as orders_router
from app.api.segments import router as segments_router
from app.api.campaigns import router as campaigns_router
from app.api.receipts import router as receipts_router
from app.api.agent import router as agent_router

__all__ = [
    "customers_router",
    "orders_router",
    "segments_router",
    "campaigns_router",
    "receipts_router",
    "agent_router",
]
