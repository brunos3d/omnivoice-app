"""Voice lookup helpers.

External surfaces (public API, SDKs, Copy-Voice-ID) address voices by their stable
``public_voice_id``; internal code uses the UUID primary key. These helpers centralize
both lookups so future API work has a single entry point.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import VoiceProfile


async def get_voice_by_public_id(
    db: AsyncSession, public_voice_id: str
) -> Optional[VoiceProfile]:
    """Resolve a voice by its public, stable identifier (the external contract)."""
    result = await db.execute(
        select(VoiceProfile).where(VoiceProfile.public_voice_id == public_voice_id)
    )
    return result.scalar_one_or_none()


async def get_voice_by_internal_id(
    db: AsyncSession, voice_id: str
) -> Optional[VoiceProfile]:
    """Resolve a voice by its internal UUID primary key."""
    return await db.get(VoiceProfile, voice_id)


async def public_id_exists(db: AsyncSession, public_voice_id: str) -> bool:
    """True when a public_voice_id is already taken (used for collision-safe generation)."""
    result = await db.execute(
        select(VoiceProfile.id).where(VoiceProfile.public_voice_id == public_voice_id)
    )
    return result.first() is not None
