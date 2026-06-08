"""TDD: E2E validation scaffolding for the runtime-service path (2C.4).

This file is the SCAFFOLDING for the provider-validated E2E test
that runs in the CI lane where a real ``peakvox/kokoro-runtime``
container is available. The test is gated:

  - In the default test venv (no docker compose, no real
    container), the test is **skipped**.
  - When ``KOKORO_RUNTIME_URL`` is set to a reachable URL, the
    test runs end-to-end through the KokoroAdapter's
    runtime-service path.

The test verifies that the full chain works:
  - HTTPTransport -> Runtime Service Contract
  - /v1/generate endpoint
  - Audio base64 + duration + logs response
  - (duration, logs) tuple contract
  - File written to output_path

The test is NOT a synthetic mock test — it requires a real
runtime service. Per the Phase 2C validation strategy, this
test is gated to a CI lane where docker compose is available.

For Phase 2D, the test will be wired into the CI pipeline. For
now, it is a placeholder that documents the expected E2E shape.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest


# The test is gated on the runtime URL being set. In the test venv
# the URL is not set; the test is skipped.
KOKORO_RUNTIME_URL_ENV = "KOKORO_RUNTIME_URL"


def _runtime_url() -> str:
    return os.environ.get(KOKORO_RUNTIME_URL_ENV, "").strip()


pytestmark = pytest.mark.skipif(
    not _runtime_url(),
    reason=(
        "E2E test gated on KOKORO_RUNTIME_URL being set. In the test "
        "venv the URL is empty; the test is skipped. To run this "
        "test locally: start the runtime service (Phase 2D) and "
        "export KOKORO_RUNTIME_URL=http://<host>:<port>."
    ),
)


@pytest.fixture
def output_path(tmp_path) -> Path:
    return tmp_path / "kokoro_e2e_output.wav"


def test_kokoro_runtime_service_e2e_generates_audio(output_path) -> None:
    """End-to-end: PeakVox backend -> KokoroAdapter -> HTTPTransport
    -> peakvox/kokoro-runtime -> audio bytes -> (duration, logs).

    This test runs when KOKORO_RUNTIME_URL is set to a reachable
    URL. The URL is expected to point to a runtime service that
    implements the Runtime Service Contract (ADR-0017 §6)."""
    from app.models.registry_types import ModelCapabilities, ModelDescriptor
    from app.services.model_adapters.kokoro_adapter import KokoroAdapter

    desc = ModelDescriptor(
        id="kokoro-base", name="Kokoro Base", description="d",
        provider="kokoro", supported_languages=["en"],
        supported_tags=[], capabilities=ModelCapabilities(supports_tts=True),
    )
    a = KokoroAdapter(desc)

    duration, logs = asyncio.run(
        a.generate(
            text="hello, world",
            output_path=output_path,
            voice_id="af_heart",
            language="en",
        )
    )

    # The runtime service is expected to return real audio
    # (per ADR-0017 §6.3).
    assert duration > 0.0
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert len(logs) >= 1
