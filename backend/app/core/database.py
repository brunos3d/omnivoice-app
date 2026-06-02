from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add generation_defaults column to existing databases that predate this field.
        # SQLite raises OperationalError on duplicate columns — safe to ignore.
        try:
            await conn.execute(
                text("ALTER TABLE voice_profiles ADD COLUMN generation_defaults JSON")
            )
        except Exception:
            pass
