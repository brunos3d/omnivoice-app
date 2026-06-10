"""Contract + regression tests for the peakvox/omnivoice-runtime server.

The OmniVoice model is mocked; the tests exercise the HTTP shape, the
readiness state machine, and — critically — the T24 regressions:

  1. Correct upstream class: ``from omnivoice import OmniVoice``
     (``OmniVoicePipeline`` does not exist; importing it crashed the
     first /v1/generate of every container).
  2. Correct inference API: ``pipeline.generate(text=..., ...)``,
     not ``synthesize``.
  3. voice_design tag lists are joined into a single instruct string
     (OmniVoice requires len(instruct list) == len(texts) == 1).
  4. The output tensor's batch dimension is squeezed before duration
     is computed — OmniVoice returns (1, N) tensors, and without the
     squeeze the reported duration is 0 ms.

torch is NOT required: a minimal fake torch module is injected into
``sys.modules`` (the server imports torch lazily inside _run_inference).
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient


_SERVER_PATH = Path(__file__).resolve().parents[1] / "server.py"


def _load_server_module():
    """Load server.py under a unique module name (no bare ``import server``,
    which would collide with the other runtimes' server modules when several
    runtime test suites run in one pytest session)."""
    spec = importlib.util.spec_from_file_location("omnivoice_base_server", _SERVER_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["omnivoice_base_server"] = mod
    spec.loader.exec_module(mod)
    return mod


srv = _load_server_module()


# ---------------------------------------------------------------------------
# Fake torch (server imports torch lazily inside _run_inference)
# ---------------------------------------------------------------------------


class _FakeTensor:
    """Mimics the tensor surface _run_inference touches:
    .cpu().float().squeeze().numpy()"""

    def __init__(self, arr: np.ndarray) -> None:
        self.arr = arr

    def cpu(self) -> "_FakeTensor":
        return self

    def float(self) -> "_FakeTensor":
        return self

    def squeeze(self) -> "_FakeTensor":
        return _FakeTensor(self.arr.squeeze())

    def numpy(self) -> np.ndarray:
        return self.arr


def _make_fake_torch() -> types.ModuleType:
    fake = types.ModuleType("torch")

    def cat(tensors: list) -> _FakeTensor:
        return _FakeTensor(np.concatenate([t.arr for t in tensors], axis=0))

    fake.cat = cat  # type: ignore[attr-defined]
    return fake


# ---------------------------------------------------------------------------
# Fake OmniVoice pipeline
# ---------------------------------------------------------------------------


class _MockOmniVoicePipeline:
    """Stand-in for ``omnivoice.OmniVoice``.

    ``generate(**kwargs)`` records its kwargs and returns a list with one
    (1, 24000) tensor — the real model's shape, batch dimension included.
    """

    SAMPLE_RATE = 24000

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate(self, **kwargs: Any) -> list:
        self.calls.append(kwargs)
        one_second = np.zeros((1, self.SAMPLE_RATE), dtype=np.float32)
        one_second[0, : self.SAMPLE_RATE // 2] = 0.1  # non-silent half
        return [_FakeTensor(one_second)]


@pytest.fixture
def pipeline() -> _MockOmniVoicePipeline:
    return _MockOmniVoicePipeline()


@pytest.fixture
def client(pipeline, monkeypatch):
    """TestClient with the pipeline injected and fake torch in sys.modules."""
    monkeypatch.setitem(sys.modules, "torch", _make_fake_torch())
    srv._pipeline = pipeline
    srv._sample_rate = _MockOmniVoicePipeline.SAMPLE_RATE
    srv._load_state = "ready"
    with TestClient(srv.app) as c:
        yield c
    srv._pipeline = None
    srv._sample_rate = None
    srv._load_state = "unloaded"
    srv._load_error = None


def _payload(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "voice_id": "voice_test",
        "text": "Hello, world.",
        "language": "auto",
        "params": {},
        "request_id": "req_t24_001",
    }
    body.update(overrides)
    return body


# ---------------------------------------------------------------------------
# Contract surface
# ---------------------------------------------------------------------------


def test_health_returns_200(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "alive"}


def test_ready_returns_200_when_loaded(client) -> None:
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready"}


def test_ready_returns_503_when_unloaded() -> None:
    srv._pipeline = None
    srv._load_state = "unloaded"
    with TestClient(srv.app) as c:
        r = c.get("/ready")
        assert r.status_code == 503
        assert r.json()["status"] == "not_ready"


def test_metadata_returns_canonical_body(client) -> None:
    r = client.get("/v1/metadata")
    assert r.status_code == 200
    body = r.json()
    assert body["runtime_id"] == "omnivoice-base"
    assert body["model_id"] == "omnivoice-base"
    assert "voice_design" in body["capabilities"]


def test_generate_returns_503_envelope_when_load_failed() -> None:
    srv._pipeline = None
    srv._load_state = "failed"
    srv._load_error = "test: simulated load failure"
    with TestClient(srv.app) as c:
        r = c.post("/v1/generate", json=_payload())
        assert r.status_code == 503
        assert r.json()["error"]["category"] == "not_ready"
    srv._load_state = "unloaded"
    srv._load_error = None


def test_build_variant_returns_501(client) -> None:
    r = client.post("/v1/variants/build", json={
        "voice_id": "voice_test",
        "reference_audio_storage_key": "voices/x/ref.wav",
        "request_id": "req_t24_b01",
    })
    assert r.status_code == 501


# ---------------------------------------------------------------------------
# T24 regression 1+2: upstream class name and inference API
# ---------------------------------------------------------------------------


def test_loader_imports_omnivoice_class_not_omnivoicepipeline() -> None:
    """The package exposes ``OmniVoice``; ``OmniVoicePipeline`` does not exist.

    The original server imported OmniVoicePipeline, so the lazy load failed
    on the first /v1/generate of every container start.
    """
    source = _SERVER_PATH.read_text()
    assert "import OmniVoicePipeline" not in source
    assert "from omnivoice import OmniVoice" in source


def test_loader_calls_from_pretrained_with_canonical_repo(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class _FakeOmniVoice:
        @classmethod
        def from_pretrained(cls, repo: str) -> Any:
            captured["repo"] = repo
            return types.SimpleNamespace(
                config=types.SimpleNamespace(sampling_rate=24000)
            )

    fake_pkg = types.ModuleType("omnivoice")
    fake_pkg.OmniVoice = _FakeOmniVoice  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "omnivoice", fake_pkg)

    try:
        srv._load_omnivoice_pipeline()
        assert captured["repo"] == "k2-fsa/OmniVoice"
        assert srv._sample_rate == 24000
    finally:
        srv._pipeline = None
        srv._sample_rate = None


def test_inference_uses_generate_method(client, pipeline) -> None:
    """The pipeline method is ``generate`` (records a call), not ``synthesize``."""
    r = client.post("/v1/generate", json=_payload())
    assert r.status_code == 200
    assert len(pipeline.calls) == 1
    assert pipeline.calls[0]["text"] == "Hello, world."
    assert not hasattr(pipeline, "synthesize") or not getattr(pipeline, "synthesize", None)


# ---------------------------------------------------------------------------
# T24 regression 3: voice_design list → single instruct string
# ---------------------------------------------------------------------------


def test_voice_design_list_is_joined_into_instruct_string(client, pipeline) -> None:
    """A 3-tag voice_design list must become ONE comma-joined string.

    Passing the raw list made OmniVoice raise "should be either the number
    of the text or 1, but got 3" (instruct list length must match text count).
    """
    r = client.post("/v1/generate", json=_payload(
        params={"voice_design": ["male", "elderly", "moderate pitch"]},
    ))
    assert r.status_code == 200
    instruct = pipeline.calls[0]["instruct"]
    assert isinstance(instruct, str)
    assert instruct == "male, elderly, moderate pitch"


def test_voice_design_inside_generation_defaults_is_joined(client, pipeline) -> None:
    r = client.post("/v1/generate", json=_payload(
        params={"generation_defaults": {"voice_design": ["female", "whisper"]}},
    ))
    assert r.status_code == 200
    assert pipeline.calls[0]["instruct"] == "female, whisper"


def test_explicit_instruct_passes_through_unchanged(client, pipeline) -> None:
    r = client.post("/v1/generate", json=_payload(
        params={"instruct": "a calm narrator voice"},
    ))
    assert r.status_code == 200
    assert pipeline.calls[0]["instruct"] == "a calm narrator voice"


def test_ref_audio_and_ref_text_forwarded(client, pipeline) -> None:
    r = client.post("/v1/generate", json=_payload(
        params={"ref_audio_path": "/data/tmp/ref.wav", "ref_text": "olá mundo"},
    ))
    assert r.status_code == 200
    call = pipeline.calls[0]
    assert call["ref_audio"] == "/data/tmp/ref.wav"
    assert call["ref_text"] == "olá mundo"


def test_transcript_param_feeds_ref_text(client, pipeline) -> None:
    r = client.post("/v1/generate", json=_payload(
        params={"ref_audio_path": "/data/tmp/ref.wav", "transcript": "stored words"},
    ))
    assert r.status_code == 200
    assert pipeline.calls[0]["ref_text"] == "stored words"


def test_language_auto_is_omitted(client, pipeline) -> None:
    """language="auto" lets the model detect; it must not be forwarded."""
    r = client.post("/v1/generate", json=_payload(language="auto"))
    assert r.status_code == 200
    assert "language" not in pipeline.calls[0]


# ---------------------------------------------------------------------------
# T24 regression 4: batch-dimension squeeze → correct duration
# ---------------------------------------------------------------------------


def test_duration_header_reflects_samples_not_batch_dim(client) -> None:
    """OmniVoice returns (1, N) tensors. Without .squeeze(), len(audio) == 1
    and the reported duration is 0 ms. With the fix, a 24000-sample clip at
    24 kHz reports exactly 1000 ms."""
    r = client.post("/v1/generate", json=_payload())
    assert r.status_code == 200
    duration_ms = int(r.headers["X-Peakvox-Duration-Ms"])
    assert duration_ms == 1000  # not 0


def test_generate_returns_nonempty_wav(client) -> None:
    r = client.post("/v1/generate", json=_payload())
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/wav"
    assert r.headers["X-Peakvox-Request-Id"] == "req_t24_001"
    assert r.content[:4] == b"RIFF"
    assert len(r.content) > 44
