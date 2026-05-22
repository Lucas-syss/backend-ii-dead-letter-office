from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get(
    "/health",
    summary="Health check",
    description="Returns the current status and version of the API. Used as a liveness probe.",
    tags=["Health"],
)
async def health_check() -> dict:
    """
    Liveness probe endpoint.

    Returns 200 OK when the service is running.
    """
    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENV,
    }
