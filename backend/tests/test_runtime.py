from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)

from app.core.migrations import run_migrations
from app.models.registry_types import ModelCapabilities, ModelDescriptor
from app.services.model_adapter import ModelAdapter
from app.services.runtime import (
    PeakVoxRuntime,
    ModelNotRegistered,
    VoiceNotFound,
    VariantUnavailable,
    UnsupportedTags,
    UnsupportedCapability,
    ModelNotActive,
)

_SEED = (
    "INSERT INTO voice_profiles (id, public_voice_id, owner_id, name, audio_filename, "
    "transcript, generation_defaults, is_public, is_community_voice, is_preset_voice, "
    "is_favorite, status, usage_count, created_at, updated_at) "
    "VALUES ('uuid-1','voice_ABC123','owner-1','Bruno','voices/uuid-1/reference.wav',"
    "'olá','{}',0,0,0,0,'ready',0,'2026-01-01','2026-01-01')"
)


class FakeAdapter(ModelAdapter):
    def __init__(self, descriptor):
        super().__init__(descriptor)
        self.generated: list[str] = []

    async def install(self): ...
    async def load(self): ...
    def unload(self): ...
    async def health_check(self) -> bool:
        return True

    async def generate(self, *, text, output_path, **kwargs):
        self.generated.append(text)
        return (2.0, [f"{self.model_id}:{text}"])

    async def clone_voice(self, *, db, voice, reference_audio_key):
        raise NotImplementedError

    async def build_variant(self, *, db, voice):
        raise NotImplementedError


def _desc(model_id, *, default=False, tags=None, caps=None):
    return ModelDescriptor(
        id=model_id, name=model_id, description="d", provider="fake",
        supported_tags=tags or [], is_default=default,
        capabilities=caps or ModelCapabilities(),
    )


def _inactive_desc(model_id):
    return ModelDescriptor(
        id=model_id, name=model_id, description="d", provider="fake",
        status="inactive", capabilities=ModelCapabilities(supports_tts=True),
    )


def _runtime():
    rt = PeakVoxRuntime()
    rt.register_adapter(FakeAdapter(_desc("omnivoice-base", default=True, tags=["happy"],
                                          caps=ModelCapabilities(supports_voice_cloning=True))))
    rt.register_adapter(FakeAdapter(_desc("omnivoice-singing", tags=["singing", "whisper"],
                                          caps=ModelCapabilities(supports_singing=True))))
    return rt


@pytest.fixture
async def session(tmp_path):
    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/rt.db", future=True)
    async with eng.begin() as conn:
        await run_migrations(conn)
        await conn.execute(text(_SEED))
        await run_migrations(conn)  # backfill base variant
    maker = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s
    await eng.dispose()


def test_adapter_registry_and_default():
    rt = _runtime()
    assert rt.get_adapter("omnivoice-singing").model_id == "omnivoice-singing"
    assert rt.resolve_model(None).id == "omnivoice-base"  # default
    with pytest.raises(ModelNotRegistered):
        rt.get_adapter("nope")


async def test_resolve_voice_and_variant(session):
    rt = _runtime()
    res = await rt.resolve(session, public_voice_id="voice_ABC123", model_id="omnivoice-base")
    assert res.voice.id == "uuid-1"
    assert res.model.id == "omnivoice-base"
    assert res.variant is not None
    assert res.adapter.model_id == "omnivoice-base"


async def test_resolve_unknown_voice_raises(session):
    rt = _runtime()
    with pytest.raises(VoiceNotFound):
        await rt.resolve(session, public_voice_id="voice_NOPE", model_id="omnivoice-base")


async def test_resolve_missing_variant_raises(session):
    rt = _runtime()
    with pytest.raises(VariantUnavailable):
        await rt.resolve(session, public_voice_id="voice_ABC123", model_id="omnivoice-singing")


def test_validate_tags_is_capability_data_driven():
    rt = _runtime()
    assert rt.validate_tags("omnivoice-base", "hello [happy]") == []
    bad = rt.validate_tags("omnivoice-base", "sing [singing] now")
    assert "singing" in bad


def test_validate_capabilities_reports_missing():
    rt = _runtime()
    assert rt.missing_capabilities("omnivoice-base", {"supports_voice_cloning"}) == set()
    assert rt.missing_capabilities("omnivoice-base", {"supports_singing"}) == {"supports_singing"}


async def test_generate_adhoc_without_voice(session):
    rt = _runtime()
    duration, logs = await rt.generate(
        session, text="hi", model_id="omnivoice-base", output_path=Path("/tmp/x.wav")
    )
    assert duration == 2.0
    assert "omnivoice-base:hi" in logs[0]


async def test_generate_rejects_unsupported_tags(session):
    rt = _runtime()
    with pytest.raises(UnsupportedTags):
        await rt.generate(
            session, text="x [singing]", model_id="omnivoice-base", output_path=Path("/tmp/x.wav")
        )


async def test_generate_rejects_unsupported_capability(session):
    rt = _runtime()
    with pytest.raises(UnsupportedCapability):
        await rt.generate(
            session, text="hi", model_id="omnivoice-base", output_path=Path("/tmp/x.wav"),
            required_capabilities={"supports_singing"},
        )


async def test_generate_rejects_inactive_model(session):
    rt = PeakVoxRuntime()
    rt.register_adapter(FakeAdapter(_inactive_desc("inactive-model")))
    with pytest.raises(ModelNotActive):
        await rt.generate(
            session, text="hi", model_id="inactive-model", output_path=Path("/tmp/x.wav")
        )


# ── Regression: model_id is NEVER replaced by the default ──────────────────

def test_resolve_model_explicit_is_not_overridden_by_default():
    """When model_id is provided explicitly, resolve_model MUST return that model,
    never the default (regression: the bug sent omnivoice-singing tags to omnivoice-base)."""
    rt = _runtime()
    # The default is "omnivoice-base", but explicit request gets the exact model.
    assert rt.resolve_model("omnivoice-singing").id == "omnivoice-singing"
    assert rt.resolve_model("omnivoice-base").id == "omnivoice-base"


def test_validate_tags_uses_the_specified_model_not_the_default():
    """Tag validation for each model uses only that model's tag list.
    Base model rejects singing tags; singing model accepts them."""
    rt = _runtime()
    # Base model: singing tags are unsupported.
    assert "singing" in rt.validate_tags("omnivoice-base", "[singing]")
    assert "whisper" in rt.validate_tags("omnivoice-base", "[whisper]")
    # Singing model: singing tags are supported.
    assert rt.validate_tags("omnivoice-singing", "[singing]") == []
    assert rt.validate_tags("omnivoice-singing", "[whisper]") == []


def test_validate_tags_singing_accepts_its_own_tags():
    """Singing model accepts tags from its own declared tag list (singing, whisper),
    proving validate_tags uses the specified model's tags, not the default's."""
    rt = _runtime()
    for tag in ["singing", "whisper"]:
        assert rt.validate_tags("omnivoice-singing", f"[{tag}]") == [], (
            f"singing model should accept [{tag}]"
        )


def test_validate_tags_base_rejects_singing_specific_tags():
    """Base model (omnivoice-base) rejects tags only declared on the singing model
    because capabilities should always come from the selected model."""
    rt = _runtime()
    # "singing" and "whisper" are only in the singing model's tag list in the test helper.
    for tag in ["singing", "whisper"]:
        bad = rt.validate_tags("omnivoice-base", f"[{tag}]")
        assert tag in bad, f"base model should reject [{tag}]"


async def test_generate_uses_singing_model_tags_not_default(session):
    """Runtime.generate MUST validate tags against the explicitly specified
    model, not the platform default (the exact regression from the bug report)."""
    rt = _runtime()
    # omnivoice-singing should accept [singing] tags (no exception).
    duration, logs = await rt.generate(
        session, text="sing [singing] for me", model_id="omnivoice-singing",
        output_path=Path("/tmp/x.wav"),
    )
    assert duration == 2.0
    assert "omnivoice-singing" in logs[0]


def test_voice_id_constant_while_model_changes():
    """Regression: Voice identity is constant; capabilities and tags follow
    the model. Proves the Universal Voice Runtime thesis works correctly:
    same Voice ID + different Models + different tags."""
    rt = _runtime()
    VOICE = "voice_ABC123"

    # Tag behavior follows the model (capability-driven, not voice-driven).
    assert "singing" in rt.validate_tags("omnivoice-base", "[singing]")
    assert rt.validate_tags("omnivoice-singing", "[singing]") == []

    # Capabilities follow the model (same Voice ID, different capabilities).
    assert rt.missing_capabilities("omnivoice-base", {"supports_singing"}) == {"supports_singing"}
    assert rt.missing_capabilities("omnivoice-singing", {"supports_singing"}) == set()

    # Model resolution respects explicit model_id (never replaced by default).
    assert rt.resolve_model("omnivoice-base").id == "omnivoice-base"
    assert rt.resolve_model("omnivoice-singing").id == "omnivoice-singing"
