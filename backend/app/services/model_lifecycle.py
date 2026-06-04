"""Persisted model lifecycle transitions.

Operates on the ``models`` table (the first-class entity). The in-memory registry is refreshed
from the DB by the wiring layer; these functions are the source of truth for status changes.
"""

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ModelNotFoundError(Exception):
    pass


async def _set_status(session: AsyncSession, model_id: str, status: str, *, deprecated: bool = False) -> None:
    now = datetime.now(timezone.utc).isoformat()
    res = await session.execute(text("SELECT id FROM models WHERE id=:id"), {"id": model_id})
    if res.first() is None:
        raise ModelNotFoundError(model_id)
    if deprecated:
        await session.execute(
            text("UPDATE models SET status=:s, deprecated_at=:t, updated_at=:t WHERE id=:id"),
            {"s": status, "t": now, "id": model_id},
        )
    else:
        await session.execute(
            text("UPDATE models SET status=:s, updated_at=:t WHERE id=:id"),
            {"s": status, "t": now, "id": model_id},
        )
    await session.commit()


async def activate_model(session: AsyncSession, model_id: str) -> None:
    await _set_status(session, model_id, "available")


async def deactivate_model(session: AsyncSession, model_id: str) -> None:
    await _set_status(session, model_id, "disabled")


async def deprecate_model(session: AsyncSession, model_id: str) -> None:
    await _set_status(session, model_id, "deprecated", deprecated=True)
