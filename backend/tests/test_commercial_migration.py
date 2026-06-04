import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.migrations import run_migrations

COMMERCIAL_TABLES = [
    "roles", "creators", "marketplace_listings",
    "credit_ledgers", "transactions", "royalties", "payouts",
]


@pytest.fixture
async def engine(tmp_path):
    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/commercial.db", future=True)
    yield eng
    await eng.dispose()


async def _table_names(engine):
    async with engine.begin() as conn:
        res = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        return {row[0] for row in res.fetchall()}


async def test_commercial_tables_created(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)
    assert set(COMMERCIAL_TABLES) <= await _table_names(engine)


async def test_commercial_tables_empty_in_community(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)
    async with engine.begin() as conn:
        for table in COMMERCIAL_TABLES:
            res = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            assert res.scalar() == 0, f"{table} should be empty in CE"


async def test_migration_is_idempotent(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)
    async with engine.begin() as conn:
        await run_migrations(conn)  # must not raise
    assert set(COMMERCIAL_TABLES) <= await _table_names(engine)
