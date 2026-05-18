from fastapi import APIRouter

from app.api.v1 import health, events, incidents

router = APIRouter()

# Health
router.include_router(health.router)

# Events
router.include_router(
    events.router,
    prefix="/events",
    tags=["Events"],
)

# Incidents
router.include_router(
    incidents.router,
    prefix="/incidents",
    tags=["Incidents"],
)