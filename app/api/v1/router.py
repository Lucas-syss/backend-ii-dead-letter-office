from fastapi import APIRouter

from app.api.v1 import health, events

router = APIRouter()

# Health
router.include_router(health.router)

# Events
router.include_router(
    events.router,
    prefix="/events",
    tags=["Events"],
)