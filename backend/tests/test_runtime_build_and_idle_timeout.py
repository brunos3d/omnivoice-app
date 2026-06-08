"""TDD: spec.build block (R2) + spec.lifecycle.idle_timeout (R7).

These two refinements were applied to RuntimeDescriptor after the
Runtime Service Readiness Audit. They are infrastructure-level
schema changes; the manager still never reads ``spec.build``,
but the field must parse and round-trip cleanly.

Vocabulary
----------

RUNTIME_IDLE_TIMEOUT_VOCABULARY is the closed set of values for
``spec.lifecycle.idle_timeout`` (R7):

  - "never"   (Cloud default; the autoscaler owns lifecycle)
  - "15m"     (Community Edition default)
  - "30m"
  - "1h"
  - "6h"

Any other value is rejected at descriptor load time.

The ``spec.build`` block is optional. When present, it carries
the local-build metadata (CE flow). The ``RuntimeManager`` never
reads it; the registry loader / build script is the only
consumer.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.runtime_types import (
    RUNTIME_IDLE_TIMEOUT_VOCABULARY,
    RuntimeBuild,
    RuntimeDescriptor,
    parse_idle_timeout_to_seconds,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _good_descriptor() -> dict:
    return {
        "api_version": "peakvox.io/v1",
        "kind": "Runtime",
        "metadata": {
            "id": "kokoro-82m",
            "name": "Kokoro 82M Runtime",
            "provider": "kokoro",
            "version": "0.1.0",
            "edition": ["ce"],
        },
        "spec": {
            "runtime_type": "docker",
            "image": {
                "repository": "peakvox/kokoro-runtime",
                "tag": "0.1.0",
            },
            "service": {
                "protocol": "http",
                "port": 8000,
            },
            "capabilities": ["tts"],
            "requirements": {
                "gpu": "none",
                "min_vram_gb": 0,
                "cpu_cores": 1,
                "memory_gb": 2,
                "edition": ["ce"],
            },
            "model_binding": {
                "model_id": "kokoro-base",
                "is_default": True,
                "priority": 100,
            },
        },
    }


# ---------------------------------------------------------------------------
# spec.build — R2
# ---------------------------------------------------------------------------


def test_runtime_build_block_parses() -> None:
    """A spec.build block parses cleanly when present."""
    payload = _good_descriptor()
    payload["spec"]["build"] = {
        "entrypoint": "server.py",
        "build_context": ".",
        "dockerfile": "Dockerfile",
    }
    d = RuntimeDescriptor.model_validate(payload)
    assert d.spec.build is not None
    assert d.spec.build.entrypoint == "server.py"
    assert d.spec.build.build_context == "."
    assert d.spec.build.dockerfile == "Dockerfile"


def test_runtime_build_block_default_dockerfile() -> None:
    """The default dockerfile is 'Dockerfile' when omitted."""
    payload = _good_descriptor()
    payload["spec"]["build"] = {
        "entrypoint": "server.py",
        "build_context": ".",
    }
    d = RuntimeDescriptor.model_validate(payload)
    assert d.spec.build is not None
    assert d.spec.build.dockerfile == "Dockerfile"


def test_runtime_build_block_is_optional() -> None:
    """A descriptor without spec.build is valid (Cloud flow)."""
    d = RuntimeDescriptor.model_validate(_good_descriptor())
    assert d.spec.build is None


def test_runtime_build_block_rejects_absolute_entrypoint() -> None:
    """An absolute entrypoint path is rejected (path-traversal guard)."""
    payload = _good_descriptor()
    payload["spec"]["build"] = {
        "entrypoint": "/server.py",
        "build_context": ".",
    }
    with pytest.raises(ValidationError) as exc_info:
        RuntimeDescriptor.model_validate(payload)
    assert "entrypoint" in str(exc_info.value).lower()


def test_runtime_build_block_rejects_absolute_build_context() -> None:
    """An absolute build_context is rejected (path-traversal guard)."""
    payload = _good_descriptor()
    payload["spec"]["build"] = {
        "entrypoint": "server.py",
        "build_context": "/opt/build",
    }
    with pytest.raises(ValidationError) as exc_info:
        RuntimeDescriptor.model_validate(payload)
    assert "build_context" in str(exc_info.value).lower()


def test_runtime_build_block_requires_entrypoint() -> None:
    """An empty entrypoint is rejected."""
    with pytest.raises(ValidationError):
        RuntimeBuild(entrypoint="", build_context=".")


def test_runtime_build_block_requires_build_context() -> None:
    """An empty build_context is rejected."""
    with pytest.raises(ValidationError):
        RuntimeBuild(entrypoint="server.py", build_context="")


def test_runtime_build_block_does_not_change_image() -> None:
    """The build block is independent of the image block; both are present
    and the image identity is the source of truth for the manager."""
    payload = _good_descriptor()
    payload["spec"]["build"] = {
        "entrypoint": "server.py",
        "build_context": ".",
    }
    d = RuntimeDescriptor.model_validate(payload)
    assert d.spec.image.repository == "peakvox/kokoro-runtime"
    assert d.spec.image.tag == "0.1.0"
    assert d.spec.build is not None


# ---------------------------------------------------------------------------
# spec.lifecycle.idle_timeout — R7
# ---------------------------------------------------------------------------


def test_idle_timeout_default_is_15m() -> None:
    """The default idle_timeout is '15m' (CE default)."""
    d = RuntimeDescriptor.model_validate(_good_descriptor())
    assert d.spec.lifecycle.idle_timeout == "15m"


@pytest.mark.parametrize("value", sorted(RUNTIME_IDLE_TIMEOUT_VOCABULARY))
def test_idle_timeout_accepts_vocabulary(value: str) -> None:
    """Every entry in the closed vocabulary is accepted."""
    payload = _good_descriptor()
    payload["spec"]["lifecycle"] = {"idle_timeout": value}
    d = RuntimeDescriptor.model_validate(payload)
    assert d.spec.lifecycle.idle_timeout == value


def test_idle_timeout_rejects_unknown_value() -> None:
    """A value outside the closed vocabulary is rejected."""
    payload = _good_descriptor()
    payload["spec"]["lifecycle"] = {"idle_timeout": "5m"}  # not in vocabulary
    with pytest.raises(ValidationError) as exc_info:
        RuntimeDescriptor.model_validate(payload)
    assert "idle_timeout" in str(exc_info.value).lower()


def test_idle_timeout_rejects_numeric_seconds() -> None:
    """Numeric seconds (e.g. '900') are not in the closed vocabulary."""
    payload = _good_descriptor()
    payload["spec"]["lifecycle"] = {"idle_timeout": "900"}
    with pytest.raises(ValidationError):
        RuntimeDescriptor.model_validate(payload)


# ---------------------------------------------------------------------------
# parse_idle_timeout_to_seconds — R7 helper
# ---------------------------------------------------------------------------


def test_parse_idle_timeout_to_seconds_never_returns_none() -> None:
    """The 'never' sentinel returns None (do-not-reap)."""
    assert parse_idle_timeout_to_seconds("never") is None


@pytest.mark.parametrize("value,expected", [
    ("15m", 15 * 60),
    ("30m", 30 * 60),
    ("1h", 60 * 60),
    ("6h", 6 * 60 * 60),
])
def test_parse_idle_timeout_to_seconds_converts_vocabulary(
    value: str, expected: int
) -> None:
    """Vocabulary entries convert to their canonical second count."""
    assert parse_idle_timeout_to_seconds(value) == expected


def test_parse_idle_timeout_to_seconds_rejects_unknown() -> None:
    """Unknown vocabulary entries raise ValueError."""
    with pytest.raises(ValueError) as exc_info:
        parse_idle_timeout_to_seconds("5m")
    assert "unknown" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Round-trip: descriptor with build + idle_timeout serializes identically
# ---------------------------------------------------------------------------


def test_descriptor_with_build_and_idle_timeout_round_trips() -> None:
    """A descriptor carrying both refinements round-trips through
    model_dump → model_validate without loss."""
    payload = _good_descriptor()
    payload["spec"]["build"] = {
        "entrypoint": "server.py",
        "build_context": ".",
        "dockerfile": "Dockerfile",
    }
    payload["spec"]["lifecycle"] = {"idle_timeout": "30m"}

    d1 = RuntimeDescriptor.model_validate(payload)
    dumped = d1.model_dump()
    d2 = RuntimeDescriptor.model_validate(dumped)

    assert d1.spec.build is not None
    assert d2.spec.build is not None
    assert d1.spec.build.entrypoint == d2.spec.build.entrypoint
    assert d1.spec.build.build_context == d2.spec.build.build_context
    assert d1.spec.build.dockerfile == d2.spec.build.dockerfile
    assert d1.spec.lifecycle.idle_timeout == d2.spec.lifecycle.idle_timeout
    assert d1.spec.image.repository == d2.spec.image.repository
    assert d1.spec.image.tag == d2.spec.image.tag
