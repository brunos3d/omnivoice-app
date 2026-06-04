"""The PeakVox thesis, validated end-to-end (Phase 3.7 success criterion):

A single Voice ID resolves to DIFFERENT VoiceVariants through DIFFERENT model adapters via ONE
Runtime abstraction. The Voice remains constant; the Variant changes; the Runtime resolves
everything. This is what makes PeakVox a Universal Voice Runtime rather than a model frontend.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)

from app.core.migrations import run_migrations
from app.services.model_adapters.omnivoice_adapter import (
    OmniVoiceAdapter,
    OmniVoiceSingingAdapter,
)
from app.services.model_catalog import builtin_by_id
from app.services.runtime import PeakVoxRuntime

_SEED = (
    "INSERT INTO voice_profiles (id, public_voice_id, owner_id, name, audio_filename, "
    "transcript, generation_defaults, is_public, is_community_voice, is_preset_voice, "
    "is_favorite, status, usage_count, created_at, updated_at) "
    "VALUES ('uuid-1','voice_8JXQ29K4L3','owner-1','Bruno','voices/uuid-1/reference.wav',"
    "'olá','{}',0,0,0,0,'ready',0,'2026-01-01','2026-01-01')"
)


@pytest.fixture
async def session(tmp_path):
    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/mm.db", future=True)
    async with eng.begin() as conn:
        await run_migrations(conn)
        await conn.execute(text(_SEED))
        await run_migrations(conn)  # backfill the omnivoice-base variant
    maker = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s
    await eng.dispose()


def _runtime() -> PeakVoxRuntime:
    rt = PeakVoxRuntime()
    rt.register_adapter(OmniVoiceAdapter(builtin_by_id("omnivoice-base")))
    rt.register_adapter(OmniVoiceSingingAdapter(builtin_by_id("omnivoice-singing")))
    return rt


async def test_same_voice_id_resolves_to_different_variants(session):
    rt = _runtime()
    VOICE = "voice_8JXQ29K4L3"

    # The singing variant is built on demand from the same Voice's canonical reference.
    voice = await rt.resolve(session, public_voice_id=VOICE, model_id="omnivoice-base")
    await rt.get_adapter("omnivoice-singing").build_variant(db=session, voice=voice.voice)

    base = await rt.resolve(session, public_voice_id=VOICE, model_id="omnivoice-base")
    singing = await rt.resolve(session, public_voice_id=VOICE, model_id="omnivoice-singing")

    # Same Voice (identity constant) ...
    assert base.voice.public_voice_id == VOICE == singing.voice.public_voice_id
    assert base.voice.id == singing.voice.id

    # ... different Model + Variant (realization changes) ...
    assert base.model.id == "omnivoice-base"
    assert singing.model.id == "omnivoice-singing"
    assert base.variant.id != singing.variant.id
    assert base.variant.model_id == "omnivoice-base"
    assert singing.variant.model_id == "omnivoice-singing"

    # ... and the same Runtime resolved both, through different adapters.
    assert isinstance(base.adapter, OmniVoiceAdapter)
    assert isinstance(singing.adapter, OmniVoiceSingingAdapter)


async def test_capabilities_follow_the_model_not_the_voice(session):
    rt = _runtime()
    # The Voice has no capabilities — capabilities belong to the Model (ADR-0003/0004).
    assert rt.missing_capabilities("omnivoice-base", {"supports_singing"}) == {"supports_singing"}
    assert rt.missing_capabilities("omnivoice-singing", {"supports_singing"}) == set()
