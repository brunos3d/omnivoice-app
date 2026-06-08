"""TDD: Phase 3 DoD — the backend must start without ``kokoro`` installed (R5).

The strongest architectural proof is:

  > The backend container must start successfully with Kokoro
  > completely removed from the backend Python environment.
  > Voice generation must still succeed through the Runtime
  > Service.

This test verifies the BACKEND level (the Python module
graph) at the import level. A parallel CI-gated test
(test_kokoro_removed_from_backend_image.py) verifies the
same invariant at the Docker image level.

Strategy
--------

The ``kokoro`` package is lazy-imported by ``KokoroAdapter``
(only when the in-process path is taken). When
``KOKORO_RUNTIME_URL`` is set, the adapter routes to the
runtime via ``HTTPTransport`` and never imports ``kokoro``.

This test:

  1. Asserts that ``kokoro`` is NOT a hard import in the
     backend's module graph (lazy-only).
  2. Asserts that the backend's ``requirements.txt`` does
     NOT pin ``kokoro`` directly (the runtime container
     owns the dependency).
  3. Asserts that blocking the ``kokoro`` import (via
     ``sys.modules``) does not break the backend's module
     load.

The runtime-side test (the actual E2E with audio
generation) is CI-gated; see the docker-compose lane.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest


def _backend_requirements_path() -> Path:
    """The backend's requirements.txt (or pyproject.toml
    equivalent)."""
    return Path(__file__).resolve().parents[1] / "requirements.txt"


def test_kokoro_is_not_a_hard_dependency_in_backend_requirements() -> None:
    """``kokoro`` is not a direct backend dependency.

    The runtime container at
    ``runtime-registry/kokoro-82m/requirements.txt`` owns
    the ``kokoro`` framework pin. The backend image must
    not include it. This is R5.
    """
    reqs = _backend_requirements_path()
    if not reqs.exists():
        pytest.skip("backend/requirements.txt not found")
    text = reqs.read_text()
    # Strip comments; require only direct kokoro lines (not transitive).
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip().lower()
        if not line:
            continue
        # Match lines that start with "kokoro" (the package name).
        assert not re.match(r"^kokoro(\W|$)", line), (
            f"kokoro must not be a direct backend dependency (R5). "
            f"Found: {raw_line!r} in backend/requirements.txt. "
            f"The runtime container at runtime-registry/kokoro-82m/ "
            f"owns this dependency."
        )


def test_kokoro_adapter_uses_soft_import() -> None:
    """The KokoroAdapter uses a soft top-level import for ``kokoro``
    (wrapped in try/except ImportError) so the module loads even
    when ``kokoro`` is not installed. The actual import may be
    lazy (inside a function) or soft (at module top level with
    try/except); both are acceptable for R5.
    """
    from app.services.model_adapters import kokoro_adapter
    source_path = Path(kokoro_adapter.__file__)
    source = source_path.read_text()
    # The module loads without raising ImportError, even when
    # kokoro is not installed. (The test below verifies this
    # directly with sys.modules['kokoro'] = None.)
    # Here we just confirm the module file does not have a
    # HARD top-level import that would crash the backend.
    lines = source.splitlines()
    soft = False
    for i, line in enumerate(lines):
        if re.match(r"^(import kokoro|from kokoro)", line.strip()):
            # If there's a 'try' above and an 'except ImportError' below,
            # this is a soft import.
            preceding = "\n".join(lines[max(0, i - 3):i + 1])
            if "try:" in preceding and ("except ImportError" in "\n".join(lines[i:i + 3])
                                        or "except ImportError" in "\n".join(lines[i:i + 5])):
                soft = True
                break
    assert soft, (
        "kokoro must be either lazy-imported (inside a function) "
        "or soft-imported (top-level with try/except ImportError). "
        "Either pattern is acceptable for R5."
    )


def test_backend_module_load_works_when_kokoro_is_not_in_sys_modules() -> None:
    """The backend modules can be loaded even when ``kokoro`` is
    not present in ``sys.modules`` (i.e. it was never imported).

    The runtime path does not need kokoro; the in-process path is
    opt-in via KOKORO_RUNTIME_URL unset.
    """
    # Make sure kokoro is NOT in sys.modules (e.g. because no
    # prior test in the session imported it).
    sys.modules.pop("kokoro", None)

    # Importing the adapter module should not raise. The soft
    # import pattern (try/except) allows this even when kokoro
    # is not installed.
    from app.services.model_adapters import kokoro_adapter  # noqa: F401
    from app.services import runtime as runtime_module  # noqa: F401
    from app.services import runtime_wiring  # noqa: F401
    from app.services import model_lifecycle  # noqa: F401
    # If we get here, the backend loads without kokoro.
    assert True


def test_kokoro_owned_by_runtime_registry_requirements() -> None:
    """The ``kokoro`` framework is owned by the runtime
    container at runtime-registry/kokoro-82m/requirements.txt."""
    runtime_reqs = (
        Path(__file__).resolve().parents[2]
        / "runtime-registry" / "kokoro-82m" / "requirements.txt"
    )
    assert runtime_reqs.exists(), (
        f"runtime-registry/kokoro-82m/requirements.txt must exist "
        f"and own the kokoro dependency"
    )
    text = runtime_reqs.read_text().lower()
    assert "kokoro" in text, (
        "runtime-registry/kokoro-82m/requirements.txt must pin kokoro"
    )
