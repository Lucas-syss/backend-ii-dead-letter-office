import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.config import settings
from app.db.base import Base
from app.db.session import engine

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    - Startup: create DB tables if they don't exist (dev convenience).
    - Shutdown: dispose the DB engine connection pool cleanly.
    """
    logger.info("Starting Dead Letter Office — ENV=%s", settings.ENV)

    if settings.ENV == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified.")

    yield

    # Shutdown
    await engine.dispose()
    logger.info("Dead Letter Office shutdown complete.")


# ── App factory ───────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="Dead Letter Office",
        description=(
            "AI-powered backend triage system for failed system events. "
            "Ingests failed webhooks, jobs, and API calls — then dispatches "
            "a CrewAI agent crew to diagnose, remediate, and report."
        ),
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "The requested resource was not found."},
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled internal server error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred."},
        )

    # ── Routers ───────────────────────────────────────────────
    app.include_router(v1_router, prefix="/api/v1")

    return app


app = create_app()
