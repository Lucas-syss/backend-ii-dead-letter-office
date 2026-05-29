from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Create the async engine
# - echo=True logs all SQL in development so you can see what's happening
# - connect_args only applies to SQLite (needed for async SQLite)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENV == "development",
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# Session factory — use this everywhere a DB session is needed
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)
