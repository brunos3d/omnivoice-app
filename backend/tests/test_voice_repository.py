import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.migrations import run_migrations
from app.models.db import VoiceProfile
from app.services.voice_repository import (
    get_voice_by_internal_id,
    get_voice_by_public_id,
    public_id_exists,
)


@pytest.fixture
async def session_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    async with engine.begin() as conn:
        await run_migrations(conn)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


async def _make_voice(session_factory, name="Test Voice"):
    async with session_factory() as session:
        voice = VoiceProfile(name=name, audio_filename="reference.wav")
        session.add(voice)
        await session.commit()
        await session.refresh(voice)
        return voice.id, voice.public_voice_id


async def test_get_voice_by_public_id_returns_match(session_factory):
    _, public_id = await _make_voice(session_factory)
    async with session_factory() as session:
        voice = await get_voice_by_public_id(session, public_id)
    assert voice is not None
    assert voice.public_voice_id == public_id


async def test_get_voice_by_public_id_returns_none_when_absent(session_factory):
    async with session_factory() as session:
        assert await get_voice_by_public_id(session, "voice_DOESNOTEX") is None


async def test_get_voice_by_internal_id_returns_match(session_factory):
    internal_id, _ = await _make_voice(session_factory)
    async with session_factory() as session:
        voice = await get_voice_by_internal_id(session, internal_id)
    assert voice is not None
    assert voice.id == internal_id


async def test_public_id_exists(session_factory):
    _, public_id = await _make_voice(session_factory)
    async with session_factory() as session:
        assert await public_id_exists(session, public_id) is True
        assert await public_id_exists(session, "voice_NOPENOPE0") is False
