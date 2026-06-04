import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.migrations import run_migrations


@pytest.fixture
async def engine(tmp_path):
    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/m.db", future=True)
    yield eng
    await eng.dispose()


async def _columns(engine, table):
    async with engine.begin() as conn:
        res = await conn.execute(text(f"PRAGMA table_info({table})"))
        return {row[1] for row in res.fetchall()}


async def test_model_metadata_columns_added(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)
    assert {"requirements", "license", "provider_metadata", "deprecated_at"} <= await _columns(engine, "models")


async def test_migration_idempotent_for_models(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)
    async with engine.begin() as conn:
        await run_migrations(conn)  # must not raise


async def test_builtin_base_model_seeded_with_license(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT license FROM models WHERE id='omnivoice-base'"))
        license_json = res.scalar()
    assert license_json is not None and "apache-2.0" in license_json
