from fastapi import APIRouter

from app.api.v1 import health

router = APIRouter()

# Health
router.include_router(health.router)

