"""TDD: Settings.RUNTIME_SERVICE_ENABLED (R3) — Phase 3 infrastructure gate.

The runtime subsystem is opt-in at backend startup. The flag
governs whether ``main.py`` lifespan instantiates the
``RuntimeRegistryLoader``, ``DockerRuntimeDriver``, and
``RuntimeManager``, and attaches the manager to
``PeakVoxRuntime``.

CE default: ``False`` (the in-process adapter path is the only
path; the Models page uses the legacy DB-status mock).
Cloud default: ``True`` (future; runtime services are the only
path in Cloud).

The flag is independent of ``KOKORO_RUNTIME_URL``. The flag is
infrastructure wiring (control plane). ``KOKORO_RUNTIME_URL`` is
adapter data-plane configuration (where the adapter sends HTTP).
"""

from __future__ import annotations

import pytest


def test_settings_runtime_service_enabled_default_is_false() -> None:
    """The default value of RUNTIME_SERVICE_ENABLED is False (CE)."""
    from app.core.config import Settings
    s = Settings()
    assert s.RUNTIME_SERVICE_ENABLED is False


def test_settings_runtime_service_enabled_can_be_enabled(monkeypatch) -> None:
    """Setting the env var RUNTIME_SERVICE_ENABLED=true flips the flag."""
    monkeypatch.setenv("RUNTIME_SERVICE_ENABLED", "true")
    from app.core.config import Settings
    s = Settings()
    assert s.RUNTIME_SERVICE_ENABLED is True


def test_settings_runtime_service_enabled_can_be_explicitly_disabled(
    monkeypatch,
) -> None:
    """An explicit 'false' env var is honored (idempotent with the
    default but operator-overridable)."""
    monkeypatch.setenv("RUNTIME_SERVICE_ENABLED", "false")
    from app.core.config import Settings
    s = Settings()
    assert s.RUNTIME_SERVICE_ENABLED is False


def test_settings_runtime_service_enabled_independent_of_kokoro_url(
    monkeypatch,
) -> None:
    """The runtime-service flag is independent of the adapter URL flag.
    Setting KOKORO_RUNTIME_URL does not imply RUNTIME_SERVICE_ENABLED.
    Setting RUNTIME_SERVICE_ENABLED does not imply KOKORO_RUNTIME_URL.
    """
    from app.core.config import Settings

    # Default: both off.
    s1 = Settings()
    assert s1.RUNTIME_SERVICE_ENABLED is False
    assert s1.KOKORO_RUNTIME_URL == ""

    # KOKORO_RUNTIME_URL set; RUNTIME_SERVICE_ENABLED still off (CE default).
    monkeypatch.setenv("KOKORO_RUNTIME_URL", "http://peakvox-kokoro-runtime:8000")
    s2 = Settings()
    assert s2.RUNTIME_SERVICE_ENABLED is False
    assert s2.KOKORO_RUNTIME_URL == "http://peakvox-kokoro-runtime:8000"

    # Both set: full runtime path.
    monkeypatch.setenv("RUNTIME_SERVICE_ENABLED", "true")
    s3 = Settings()
    assert s3.RUNTIME_SERVICE_ENABLED is True
    assert s3.KOKORO_RUNTIME_URL == "http://peakvox-kokoro-runtime:8000"


def test_settings_runtime_service_enabled_accepts_truthy_strings(
    monkeypatch,
) -> None:
    """The pydantic-settings bool parser accepts common truthy strings."""
    for truthy in ("true", "True", "1", "yes", "on"):
        monkeypatch.setenv("RUNTIME_SERVICE_ENABLED", truthy)
        from app.core.config import Settings
        s = Settings()
        assert s.RUNTIME_SERVICE_ENABLED is True, f"failed for {truthy!r}"
