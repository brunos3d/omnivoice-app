"""Public API 2.0 discovery + Generation v2 contract (ADR-0020, Task 29).

Covers the additive, backward-compatible surface:
  - model / capability / RuntimeVariant discovery endpoints
  - voice compatibility endpoints (not-found path)
  - Generation v2 request schema (new optional fields; minimal request intact)

These tests deliberately avoid running real inference (no torch/GPU in CI); they
exercise discovery, validation, and schema — not audio synthesis.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import v1 as v1_api
from app.api.v1 import require_api_key, router as v1_router
from app.core.database import get_db
from app.core.migrations import run_migrations
from app.schemas.api import TextToSpeechRequest
from app.services import runtime as runtime_module
from app.services.model_catalog import BUILTIN_MODELS
from app.services.model_registry import model_registry
from app.services.model_wiring import wire_registry


# ── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture
async def client(tmp_path):
    """v1 app with auth + db overridden; catalog seeded; no runtime manager."""
    wire_registry()
    model_registry.set_descriptors(list(BUILTIN_MODELS))
    # Ensure no manager leaks in from another test.
    runtime_module.runtime._runtime_manager = None

    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/v1.db", future=True)
    async with eng.begin() as conn:
        await run_migrations(conn)
    maker = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db():
        async with maker() as s:
            yield s

    app = FastAPI()
    app.include_router(v1_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_api_key] = lambda: None
    yield TestClient(app)
    await eng.dispose()


@pytest.fixture
def registry_dir(tmp_path: Path) -> Path:
    """Temp runtime-registry with an omnivoice runtime exposing two variants."""
    d = tmp_path / "omnivoice-base"
    (d / "variants").mkdir(parents=True)
    (d / "descriptor.json").write_text(json.dumps({
        "api_version": "peakvox.io/v1",
        "kind": "Runtime",
        "metadata": {"id": "omnivoice-base", "name": "OmniVoice", "provider": "omnivoice",
                     "version": "1.0.0", "edition": ["ce"]},
        "spec": {
            "runtime_type": "docker",
            "image": {"repository": "peakvox/omnivoice", "tag": "1.0.0"},
            "build": {"entrypoint": "server.py", "build_context": ".", "dockerfile": "Dockerfile"},
            "service": {"protocol": "http", "port": 8000},
            "capabilities": ["tts"],
            "requirements": {"gpu": "optional", "edition": ["ce"]},
            "model_binding": {"model_id": "omnivoice-base", "is_default": True, "priority": 100},
            "lifecycle": {"idle_timeout": "15m"},
        },
    }))
    (d / "variants" / "base.json").write_text(json.dumps({
        "api_version": "peakvox.io/v1", "kind": "RuntimeVariant",
        "metadata": {"id": "base", "name": "OmniVoice Base", "runtime_id": "omnivoice-base",
                     "trust": "verified"},
        "spec": {"model_binding": {"model_id": "omnivoice-base", "is_default": True},
                 "checkpoint": {"source_type": "bundled", "source_ref": "k2-fsa/OmniVoice"},
                 "is_default": True, "capabilities": ["tts", "reference_audio"]},
    }))
    (d / "variants" / "expressive.json").write_text(json.dumps({
        "api_version": "peakvox.io/v1", "kind": "RuntimeVariant",
        "metadata": {"id": "expressive", "name": "OmniVoice Expressive",
                     "runtime_id": "omnivoice-base", "trust": "community"},
        "spec": {"model_binding": {"model_id": "omnivoice-base", "is_default": False},
                 "checkpoint": {"source_type": "hf", "source_ref": "someone/omnivoice-expressive"},
                 "is_default": False, "capabilities": ["tts", "emotion_tags"]},
    }))
    return tmp_path


@pytest.fixture
async def client_with_variants(client, registry_dir):
    """Attach a real RuntimeManager so variant discovery returns descriptors."""
    from app.services.runtime_driver import RuntimeDriver
    from app.services.runtime_events import RuntimeEventBus
    from app.services.runtime_manager import RuntimeManager
    from app.services.runtime_registry import RuntimeRegistryLoader

    class _NoOpDriver(RuntimeDriver):
        async def install_runtime(self, runtime_id, descriptor): return None
        async def start_runtime(self, runtime_id): return None
        async def stop_runtime(self, runtime_id): return None
        async def update_runtime(self, runtime_id, descriptor): return None
        async def remove_runtime(self, runtime_id): return None
        async def restart_runtime(self, runtime_id): return None
        async def runtime_status(self, runtime_id): return None
        async def runtime_logs(self, runtime_id, since=None): return iter([])
        async def runtime_health(self, runtime_id): return None
        async def runtime_metrics(self, runtime_id): return None

    registry = RuntimeRegistryLoader().load_from_directory(registry_dir)
    manager = RuntimeManager(registry=registry, driver=_NoOpDriver(), events=RuntimeEventBus())
    runtime_module.runtime.attach_runtime_manager(manager)
    try:
        yield client
    finally:
        runtime_module.runtime._runtime_manager = None


# ── Model + capability discovery ─────────────────────────────────────────────
def test_list_models_returns_public_summaries(client):
    body = client.get("/api/v1/models").json()
    ids = {m["modelId"] for m in body["models"]}
    assert "omnivoice-base" in ids
    sample = next(m for m in body["models"] if m["modelId"] == "omnivoice-base")
    # Public-safe summary fields only — no repo_id / model_path internals.
    assert set(sample) == {"modelId", "name", "description", "isDefault", "languages", "defaultVariantId"}


def test_get_model_exposes_capabilities_and_settings_schema(client):
    body = client.get("/api/v1/models/omnivoice-base").json()
    assert body["capabilities"]["supports_reference_audio"] is True
    assert "speed" in body["settingsSchema"]["properties"]
    # No checkpoint / repo internals leak into the detail payload.
    assert "repo_id" not in body and "model_path" not in body


def test_get_unknown_model_404(client):
    assert client.get("/api/v1/models/does-not-exist").status_code == 404


def test_capabilities_endpoint(client):
    body = client.get("/api/v1/models/omnivoice-base/capabilities").json()
    assert body["modelId"] == "omnivoice-base"
    assert "supports_tts" in body["capabilities"]


def test_variants_empty_without_runtime_manager(client):
    body = client.get("/api/v1/models/omnivoice-base/variants").json()
    assert body == {"modelId": "omnivoice-base", "variants": []}


# ── RuntimeVariant discovery (manager attached) ──────────────────────────────
def test_list_variants_with_manager(client_with_variants):
    body = client_with_variants.get("/api/v1/models/omnivoice-base/variants").json()
    ids = [v["variantId"] for v in body["variants"]]
    assert ids[0] == "base"  # default sorts first
    assert set(ids) == {"base", "expressive"}
    base = next(v for v in body["variants"] if v["variantId"] == "base")
    assert base["isDefault"] is True
    # Public-safe: no source_ref / format / digest internals.
    assert "source_ref" not in base and "format" not in base and "digest" not in base


def test_get_single_variant_and_404(client_with_variants):
    ok = client_with_variants.get("/api/v1/models/omnivoice-base/variants/base")
    assert ok.status_code == 200 and ok.json()["variantId"] == "base"
    assert client_with_variants.get("/api/v1/models/omnivoice-base/variants/nope").status_code == 404


def test_model_detail_default_variant_id(client_with_variants):
    body = client_with_variants.get("/api/v1/models/omnivoice-base").json()
    assert body["defaultVariantId"] == "base"


# ── Compatibility (not-found path; no storage needed) ────────────────────────
def test_compatible_models_unknown_voice_404(client):
    assert client.get("/api/v1/voices/voice_DOESNOTEXIST/compatible-models").status_code == 404


def test_compatible_variants_unknown_voice_404(client):
    assert client.get("/api/v1/voices/voice_DOESNOTEXIST/compatible-variants").status_code == 404


# ── Generation v2 schema (backward compatible + additive) ────────────────────
def test_minimal_tts_request_still_valid():
    req = TextToSpeechRequest(voiceId="voice_X", text="hello")
    assert req.variantId is None
    assert req.generationSettings is None
    assert req.providerSettings is None
    assert req.format == "wav"


def test_extended_tts_request_accepts_v2_fields():
    req = TextToSpeechRequest(
        voiceId="voice_X", text="hello", modelId="omnivoice-base", variantId="base",
        language="pt", format="mp3",
        generationSettings={"speed": 1.1},
        providerSettings={"cfg_scale": 2.0, "sampling_steps": 30},
    )
    assert req.variantId == "base"
    assert req.generationSettings == {"speed": 1.1}
    assert req.providerSettings["cfg_scale"] == 2.0
