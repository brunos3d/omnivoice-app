"""TDD: KOKORO_RUNTIME_URL plumbing in Settings (2C.3).

Per Phase 2C, the runtime-service URL is a first-class settings
field. The env var ``KOKORO_RUNTIME_URL`` is read by
``pydantic_settings`` and exposed as ``settings.KOKORO_RUNTIME_URL``.

The CE default is an empty string (use the in-process path).
Cloud sets it to the runtime service URL.

These tests assert:
- The default is an empty string (CE).
- Setting the env var is reflected in the settings.
- A non-empty URL is exposed as the runtime service URL.
"""

from __future__ import annotations

import os

import pytest


def test_settings_kokoro_runtime_url_defaults_to_empty_string() -> None:
    """The CE default is the in-process path; the URL is empty."""
    # Use a clean env to avoid contamination from the host.
    env = {k: v for k, v in os.environ.items() if k != "KOKORO_RUNTIME_URL"}
    env.pop("KOKORO_RUNTIME_URL", None)
    from app.core.config import Settings
    s = Settings(_env_file=None) if hasattr(Settings, "_env_file") else Settings()
    # Default empty string when the env var is not set.
    assert s.KOKORO_RUNTIME_URL == ""


def test_settings_kokoro_runtime_url_reads_from_env(monkeypatch) -> None:
    """A non-empty env var is reflected in settings.KOKORO_RUNTIME_URL."""
    monkeypatch.setenv("KOKORO_RUNTIME_URL", "http://runtime.local:8000")
    from app.core.config import Settings
    s = Settings()
    assert s.KOKORO_RUNTIME_URL == "http://runtime.local:8000"


def test_settings_kokoro_runtime_url_can_be_https(monkeypatch) -> None:
    """Cloud deployments may use https URLs."""
    monkeypatch.setenv("KOKORO_RUNTIME_URL", "https://runtime.cloud.example.com:443")
    from app.core.config import Settings
    s = Settings()
    assert s.KOKORO_RUNTIME_URL == "https://runtime.cloud.example.com:443"
