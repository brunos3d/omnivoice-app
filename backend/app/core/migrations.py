"""Idempotent, SQLite-safe startup migration runner for the Community Edition.

This is the deliberate, lightweight alternative to Alembic for the self-hosted SQLite
deployment. ``run_migrations`` may be executed any number of times with no changes to
already-migrated records and no data loss. It evolves the legacy single-user schema into
the SaaS-ready voice entity model without recreating any voice.
"""

from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.config import settings
from app.core.database import Base
from app.utils.ids import generate_unique_public_voice_id

# Importing the models registers every table on Base.metadata for create_all.
import app.models.db  # noqa: F401

# New voice_profiles columns and their SQLite-safe DDL. NOT NULL columns carry a DEFAULT
# so existing rows are populated immediately; nullable ones are backfilled below.
_NEW_VOICE_COLUMNS: list[tuple[str, str]] = [
    # Predates Phase 2 — kept so very old databases still converge.
    ("generation_defaults", "ALTER TABLE voice_profiles ADD COLUMN generation_defaults JSON"),
    ("public_voice_id", "ALTER TABLE voice_profiles ADD COLUMN public_voice_id VARCHAR(32)"),
    ("owner_id", "ALTER TABLE voice_profiles ADD COLUMN owner_id VARCHAR(36)"),
    ("language_code", "ALTER TABLE voice_profiles ADD COLUMN language_code VARCHAR(16)"),
    ("preset_tags", "ALTER TABLE voice_profiles ADD COLUMN preset_tags JSON"),
    ("characteristics", "ALTER TABLE voice_profiles ADD COLUMN characteristics JSON"),
    ("is_public", "ALTER TABLE voice_profiles ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT 0"),
    ("is_community_voice", "ALTER TABLE voice_profiles ADD COLUMN is_community_voice BOOLEAN NOT NULL DEFAULT 0"),
    ("is_preset_voice", "ALTER TABLE voice_profiles ADD COLUMN is_preset_voice BOOLEAN NOT NULL DEFAULT 0"),
    ("is_favorite", "ALTER TABLE voice_profiles ADD COLUMN is_favorite BOOLEAN NOT NULL DEFAULT 0"),
    ("status", "ALTER TABLE voice_profiles ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'ready'"),
    ("usage_count", "ALTER TABLE voice_profiles ADD COLUMN usage_count INTEGER NOT NULL DEFAULT 0"),
    ("updated_at", "ALTER TABLE voice_profiles ADD COLUMN updated_at DATETIME"),
]

# Matches SQLAlchemy's auto-generated name (ix_<table>_<column>) so fresh installs — where
# create_all already built the unique index — converge with the IF NOT EXISTS path here.
_PUBLIC_ID_INDEX = (
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_voice_profiles_public_voice_id "
    "ON voice_profiles (public_voice_id)"
)


async def run_migrations(conn: AsyncConnection) -> None:
    """Bring the database up to the current schema. Idempotent and safe to re-run."""
    # 1. Create any missing tables (users, generation_jobs, and voice_profiles on fresh installs).
    await conn.run_sync(Base.metadata.create_all)

    # 2. Additively add new voice_profiles columns to pre-existing databases.
    await _add_missing_columns(conn)

    # 3. Seed the single implicit local owner.
    await _seed_local_owner(conn)

    # 4. Backfill legacy rows that predate the new columns.
    await _backfill_voice_profiles(conn)

    # 5. Enforce public_voice_id uniqueness (after backfill — order matters).
    await conn.execute(text(_PUBLIC_ID_INDEX))


async def _existing_voice_columns(conn: AsyncConnection) -> set[str]:
    res = await conn.execute(text("PRAGMA table_info(voice_profiles)"))
    return {row[1] for row in res.fetchall()}


async def _add_missing_columns(conn: AsyncConnection) -> None:
    existing = await _existing_voice_columns(conn)
    for column, ddl in _NEW_VOICE_COLUMNS:
        if column in existing:
            continue
        try:
            await conn.execute(text(ddl))
        except Exception:  # pragma: no cover - duplicate column on a racing run
            logger.debug("Column {} already present, skipping", column)


async def _seed_local_owner(conn: AsyncConnection) -> None:
    res = await conn.execute(
        text("SELECT id FROM users WHERE id = :id"), {"id": settings.LOCAL_OWNER_ID}
    )
    if res.first() is not None:
        return
    await conn.execute(
        text(
            "INSERT INTO users (id, handle, display_name, email, is_system, created_at) "
            "VALUES (:id, :handle, :display_name, NULL, 1, :created_at)"
        ),
        {
            "id": settings.LOCAL_OWNER_ID,
            "handle": settings.LOCAL_OWNER_HANDLE,
            "display_name": settings.LOCAL_OWNER_DISPLAY_NAME,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


async def _backfill_voice_profiles(conn: AsyncConnection) -> None:
    # Scalar backfills only touch rows still holding NULLs — already-migrated rows untouched.
    await conn.execute(
        text("UPDATE voice_profiles SET owner_id = :owner WHERE owner_id IS NULL"),
        {"owner": settings.LOCAL_OWNER_ID},
    )
    await conn.execute(text("UPDATE voice_profiles SET status = 'ready' WHERE status IS NULL"))
    await conn.execute(text("UPDATE voice_profiles SET usage_count = 0 WHERE usage_count IS NULL"))
    await conn.execute(
        text("UPDATE voice_profiles SET updated_at = created_at WHERE updated_at IS NULL")
    )

    # Per-row stable public_voice_id for legacy voices, guaranteed unique within the table.
    taken_res = await conn.execute(
        text("SELECT public_voice_id FROM voice_profiles WHERE public_voice_id IS NOT NULL")
    )
    taken = {row[0] for row in taken_res.fetchall()}

    missing_res = await conn.execute(
        text("SELECT id FROM voice_profiles WHERE public_voice_id IS NULL")
    )
    for (voice_id,) in missing_res.fetchall():
        new_id = generate_unique_public_voice_id(exists=lambda v: v in taken)
        taken.add(new_id)
        await conn.execute(
            text("UPDATE voice_profiles SET public_voice_id = :pid WHERE id = :id"),
            {"pid": new_id, "id": voice_id},
        )
