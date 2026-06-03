import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.migrations import run_migrations

# The pre-Phase-2 voice_profiles schema, exactly as it existed before this work.
OLD_SCHEMA = """
CREATE TABLE voice_profiles (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    language VARCHAR(64),
    transcript TEXT,
    audio_filename VARCHAR(255) NOT NULL,
    audio_duration FLOAT,
    meta JSON,
    generation_defaults JSON,
    created_at DATETIME,
    last_used_at DATETIME
)
"""

NEW_COLUMNS = {
    "public_voice_id",
    "owner_id",
    "language_code",
    "preset_tags",
    "characteristics",
    "is_public",
    "is_community_voice",
    "is_preset_voice",
    "is_favorite",
    "status",
    "usage_count",
    "updated_at",
}


@pytest.fixture
async def engine(tmp_path):
    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    yield eng
    await eng.dispose()


async def _seed_old_db(engine, rows):
    async with engine.begin() as conn:
        await conn.execute(text(OLD_SCHEMA))
        for r in rows:
            await conn.execute(
                text(
                    "INSERT INTO voice_profiles (id, name, audio_filename, created_at) "
                    "VALUES (:id, :name, :af, :ca)"
                ),
                r,
            )


async def _migrate(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)


async def _columns(engine):
    async with engine.connect() as conn:
        res = await conn.execute(text("PRAGMA table_info(voice_profiles)"))
        return {row[1] for row in res.fetchall()}


async def _fetchall(engine, sql, params=None):
    async with engine.connect() as conn:
        res = await conn.execute(text(sql), params or {})
        return res.mappings().all()


_LEGACY = {
    "id": "legacy-1",
    "name": "Legacy Voice",
    "af": "reference.wav",
    "ca": "2025-01-01T00:00:00+00:00",
}


async def test_migrate_old_database_adds_columns_and_backfills(engine):
    await _seed_old_db(engine, [_LEGACY])
    await _migrate(engine)

    assert NEW_COLUMNS.issubset(await _columns(engine))

    [row] = await _fetchall(engine, "SELECT * FROM voice_profiles WHERE id='legacy-1'")
    assert row["public_voice_id"].startswith("voice_")
    assert row["owner_id"] == settings.LOCAL_OWNER_ID
    assert row["status"] == "ready"
    assert row["usage_count"] == 0
    assert row["updated_at"] is not None
    # Original data preserved.
    assert row["name"] == "Legacy Voice"
    assert row["audio_filename"] == "reference.wav"


async def test_local_owner_is_seeded(engine):
    await _seed_old_db(engine, [_LEGACY])
    await _migrate(engine)

    owners = await _fetchall(engine, "SELECT * FROM users WHERE id=:id", {"id": settings.LOCAL_OWNER_ID})
    assert len(owners) == 1
    assert owners[0]["handle"] == settings.LOCAL_OWNER_HANDLE
    assert owners[0]["is_system"]


async def test_migration_is_idempotent(engine):
    await _seed_old_db(engine, [_LEGACY])
    await _migrate(engine)
    [before] = await _fetchall(engine, "SELECT public_voice_id FROM voice_profiles WHERE id='legacy-1'")

    await _migrate(engine)  # run again
    rows = await _fetchall(engine, "SELECT public_voice_id FROM voice_profiles WHERE id='legacy-1'")
    owners = await _fetchall(engine, "SELECT id FROM users WHERE id=:id", {"id": settings.LOCAL_OWNER_ID})

    assert len(rows) == 1
    assert rows[0]["public_voice_id"] == before["public_voice_id"]  # not regenerated
    assert len(owners) == 1  # owner not duplicated


async def test_public_voice_id_is_unique_across_many_legacy_rows(engine):
    rows = [
        {"id": f"legacy-{i}", "name": f"V{i}", "af": "reference.wav", "ca": _LEGACY["ca"]}
        for i in range(25)
    ]
    await _seed_old_db(engine, rows)
    await _migrate(engine)

    ids = [r["public_voice_id"] for r in await _fetchall(engine, "SELECT public_voice_id FROM voice_profiles")]
    assert len(ids) == 25
    assert all(i is not None for i in ids)
    assert len(set(ids)) == 25


async def test_fresh_database_migration_creates_all_tables(engine):
    await _migrate(engine)  # no pre-existing voice_profiles

    tables = {
        r["name"]
        for r in await _fetchall(engine, "SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"voice_profiles", "users", "generation_jobs"}.issubset(tables)
    owners = await _fetchall(engine, "SELECT id FROM users WHERE id=:id", {"id": settings.LOCAL_OWNER_ID})
    assert len(owners) == 1
