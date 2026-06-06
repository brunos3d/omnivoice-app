"""CRUD for VoicePreview records (Phase E)."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import VoicePreview


async def list_previews(
    db: AsyncSession,
    voice_id: str,
    *,
    language: Optional[str] = None,
    preview_origin: Optional[str] = None,
    source_model_id: Optional[str] = None,
) -> list[VoicePreview]:
    stmt = select(VoicePreview).where(VoicePreview.voice_id == voice_id)
    if language:
        stmt = stmt.where(VoicePreview.language == language)
    if preview_origin:
        stmt = stmt.where(VoicePreview.preview_origin == preview_origin)
    if source_model_id:
        stmt = stmt.where(VoicePreview.source_model_id == source_model_id)
    stmt = stmt.order_by(VoicePreview.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_preview_summary(
    db: AsyncSession, voice_id: str
) -> tuple[str, int, list[str]]:
    """Return ``(origin, count, languages)`` trip from VoicePreview records.

    Falls back to ``("none", 0, [])`` when no previews exist.
    The *origin* is the preview_origin of the first (most recent) preview.
    """
    previews = await list_previews(db, voice_id)
    if not previews:
        return "none", 0, []
    origin = previews[0].preview_origin
    languages = sorted({p.language for p in previews if p.language})
    return origin, len(previews), languages
