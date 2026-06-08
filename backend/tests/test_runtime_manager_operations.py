"""TDD: RuntimeManager instance cache (2D.1-2D.3).

The CE operations (install / activate / update / remove) on
the ``RuntimeManager`` cache the ``RuntimeInstance`` so that
subsequent ``start`` / ``status`` / ``resolve`` calls reuse the
cached state instead of round-tripping to the driver. The
cache is the manager's only ownership of operational state.

Architectural invariants (per the Runtime Activation Audit):

- The cache holds ``RuntimeInstance`` objects, NOT
  ``Voice`` / ``VoiceVariant`` / ``VoiceVariantArtifact``
  objects. Voices / Variants / Artifacts live in the DB layer.

- The manager never imports Docker / K8s / Podman / etc.
  The cache is populated by calling the driver.

- The cache is in-memory only; persistence is OPEN_DECISIONS
  Decision 12 (future ADR; non-blocking).

Test surface (TDD):

  2D.1 — install()
    - Reads descriptor from registry
    - Calls driver.install_runtime
    - Caches the returned RuntimeInstance
    - Returns the cached instance

  2D.2 — activate (start) / deactivate (stop)
    - activate() calls driver.start_runtime; updates cache to
      state=Active
    - deactivate() calls driver.stop_runtime; updates cache to
      state=Stopped
    - Subsequent status() returns the cached state

  2D.3 — update / remove
    - update() is stop-if-Active + re-pull; updates cache
    - remove() is stop-if-Active + clear cache

  General
    - status() reads from cache when present (no driver call)
    - resolve() returns the cached instance when one exists
      and is Active
    - Concurrent first calls for the same runtime are
      serialized (the manager is single-flight per runtime)
    - Events are published (install_requested,
      install_completed, start_requested, start_completed,
      stop_completed, remove_completed)
"""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from app.services.runtime_events import RuntimeEvent, RuntimeEventBus
from app.services.runtime_instance import (
    HealthState,
    ImageIdentity,
    RuntimeInstance,
    RuntimeState,
)
from app.services.runtime_registry import RuntimeRegistry
from app.services.runtime_types import RuntimeDescriptor, RuntimeService
from app.services.runtime_driver import RuntimeDriver
from app.services.runtime_errors import (
    RuntimeDriverError,
    RuntimeNotFound,
)


def _make_descriptor(
    *, runtime_id: str = "kokoro-82m", model_id: str = "kokoro-base"
) -> RuntimeDescriptor:
    from app.services.runtime_types import (
        RuntimeImage,
        RuntimeRequirements,
        RuntimeModelBinding,
        RuntimeLifecycle,
    )
    return RuntimeDescriptor(
        api_version="peakvox.io/v1",
        kind="Runtime",
        metadata={
            "id": runtime_id,
            "name": f"{runtime_id} runtime",
            "provider": "kokoro",
            "version": "0.1.0",
            "edition": ["ce"],
        },
        spec={
            "runtime_type": "docker",
            "image": RuntimeImage(repository="peakvox/kokoro-runtime", tag="0.1.0"),
            "service": RuntimeService(protocol="http", port=8000),
            "capabilities": ["tts"],
            "requirements": RuntimeRequirements(edition=["ce"]),
            "model_binding": RuntimeModelBinding(model_id=model_id, is_default=True, priority=100),
            "lifecycle": RuntimeLifecycle(),
        },
    )


def _make_instance(
    *, runtime_id: str = "kokoro-82m", state: RuntimeState = RuntimeState.ACTIVE
) -> RuntimeInstance:
    return RuntimeInstance(
        runtime_id=runtime_id,
        state=state,
        host="localhost",
        port=8000,
        image_identity=ImageIdentity(repository="peakvox/kokoro-runtime", tag="0.1.0", digest=None),
        started_at=datetime(2026, 6, 7, 0, 0, 0),
        last_health_at=datetime(2026, 6, 7, 0, 0, 0),
        health_state=HealthState.READY,
    )


class _FakeDriver(RuntimeDriver):
    """A minimal fake driver for 2D.1-2D.3 tests.

    Records every call; returns canned values; supports the
    full RuntimeDriver Protocol surface."""

    def __init__(self) -> None:
        self.install_calls: List[str] = []
        self.start_calls: List[str] = []
        self.stop_calls: List[str] = []
        self.update_calls: List[str] = []
        self.remove_calls: List[str] = []
        self.status_calls: List[str] = []
        self.instances: dict[str, RuntimeInstance] = {}

    async def install_runtime(self, runtime_id, descriptor):
        self.install_calls.append(runtime_id)
        inst = _make_instance(runtime_id=runtime_id, state=RuntimeState.INSTALLED)
        self.instances[runtime_id] = inst
        return inst

    async def update_runtime(self, runtime_id, descriptor):
        self.update_calls.append(runtime_id)
        return self.instances[runtime_id]

    async def remove_runtime(self, runtime_id):
        self.remove_calls.append(runtime_id)
        self.instances.pop(runtime_id, None)

    async def start_runtime(self, runtime_id):
        self.start_calls.append(runtime_id)
        inst = self.instances.get(runtime_id) or _make_instance(runtime_id=runtime_id)
        inst = RuntimeInstance(
            runtime_id=inst.runtime_id,
            state=RuntimeState.ACTIVE,
            host=inst.host,
            port=inst.port,
            image_identity=inst.image_identity,
            started_at=inst.started_at or datetime(2026, 6, 7, 0, 0, 0),
            last_health_at=inst.last_health_at or datetime(2026, 6, 7, 0, 0, 0),
            health_state=HealthState.READY,
        )
        self.instances[runtime_id] = inst
        return inst

    async def stop_runtime(self, runtime_id):
        self.stop_calls.append(runtime_id)
        inst = self.instances.get(runtime_id) or _make_instance(runtime_id=runtime_id)
        inst = RuntimeInstance(
            runtime_id=inst.runtime_id,
            state=RuntimeState.STOPPED,
            host=inst.host,
            port=inst.port,
            image_identity=inst.image_identity,
            started_at=inst.started_at,
            last_health_at=inst.last_health_at,
            health_state=HealthState.UNKNOWN,
        )
        self.instances[runtime_id] = inst

    async def restart_runtime(self, runtime_id):
        return await self.start_runtime(runtime_id)

    async def runtime_status(self, runtime_id):
        self.status_calls.append(runtime_id)
        return self.instances.get(runtime_id) or _make_instance(runtime_id=runtime_id)

    async def runtime_logs(self, runtime_id, since=None):
        async def _empty():
            if False:
                yield ""  # pragma: no cover
        return _empty()

    async def runtime_health(self, runtime_id):
        from app.services.runtime_types import HealthReport, Liveness, Readiness
        return HealthReport(
            runtime_id=runtime_id,
            liveness=Liveness.ALIVE,
            readiness=Readiness.READY,
            last_error=None,
            checked_at=datetime(2026, 6, 7, 0, 0, 0),
        )

    async def runtime_metrics(self, runtime_id):
        from app.services.runtime_types import Metrics
        return Metrics()


@pytest.fixture
def registry() -> RuntimeRegistry:
    return RuntimeRegistry([_make_descriptor()])


@pytest.fixture
def driver() -> _FakeDriver:
    return _FakeDriver()


@pytest.fixture
def events() -> RuntimeEventBus:
    return RuntimeEventBus()


# ===== 2D.1 — install() caches the instance =====


def test_install_caches_the_instance(driver, registry, events) -> None:
    """install() calls driver.install_runtime and caches the
    returned RuntimeInstance. The cached instance is returned
    to the caller."""
    import asyncio
    from app.services.runtime_manager import RuntimeManager

    mgr = RuntimeManager(registry=registry, driver=driver, events=events)
    inst = asyncio.run(mgr.install("kokoro-82m"))
    assert inst.runtime_id == "kokoro-82m"
    assert inst.state == RuntimeState.INSTALLED
    # The cache should hold the same instance.
    cached = mgr.get_cached_instance("kokoro-82m")
    assert cached is inst


def test_install_publishes_events(driver, registry, events) -> None:
    """install() publishes install_requested and install_completed."""
    import asyncio
    from app.services.runtime_manager import RuntimeManager

    seen: List[RuntimeEvent] = []
    events.subscribe(lambda e: seen.append(e))

    mgr = RuntimeManager(registry=registry, driver=driver, events=events)
    asyncio.run(mgr.install("kokoro-82m"))
    kinds = [type(e).__name__ for e in seen]
    assert "RuntimeInstallRequested" in kinds
    assert "RuntimeInstallCompleted" in kinds


def test_install_unknown_runtime_raises(driver, registry, events) -> None:
    """install() raises RuntimeNotFound for an unknown runtime_id."""
    import asyncio
    from app.services.runtime_manager import RuntimeManager

    mgr = RuntimeManager(registry=registry, driver=driver, events=events)
    with pytest.raises(RuntimeNotFound):
        asyncio.run(mgr.install("nonexistent"))


# ===== 2D.2 — activate (start) / deactivate (stop) =====


def test_start_updates_cache_to_active(driver, registry, events) -> None:
    """start() updates the cached instance to state=Active."""
    import asyncio
    from app.services.runtime_manager import RuntimeManager

    mgr = RuntimeManager(registry=registry, driver=driver, events=events)
    asyncio.run(mgr.install("kokoro-82m"))
    inst = asyncio.run(mgr.start("kokoro-82m"))
    assert inst.state == RuntimeState.ACTIVE
    cached = mgr.get_cached_instance("kokoro-82m")
    assert cached.state == RuntimeState.ACTIVE


def test_stop_updates_cache_to_stopped(driver, registry, events) -> None:
    """stop() updates the cached instance to state=Stopped."""
    import asyncio
    from app.services.runtime_manager import RuntimeManager

    mgr = RuntimeManager(registry=registry, driver=driver, events=events)
    asyncio.run(mgr.install("kokoro-82m"))
    asyncio.run(mgr.start("kokoro-82m"))
    asyncio.run(mgr.stop("kokoro-82m"))
    cached = mgr.get_cached_instance("kokoro-82m")
    assert cached.state == RuntimeState.STOPPED


def test_start_publishes_events(driver, registry, events) -> None:
    """start() publishes start_requested and start_completed."""
    import asyncio
    from app.services.runtime_manager import RuntimeManager

    seen: List[RuntimeEvent] = []
    events.subscribe(lambda e: seen.append(e))

    mgr = RuntimeManager(registry=registry, driver=driver, events=events)
    asyncio.run(mgr.install("kokoro-82m"))
    seen.clear()
    asyncio.run(mgr.start("kokoro-82m"))
    kinds = [type(e).__name__ for e in seen]
    assert "RuntimeStartRequested" in kinds
    assert "RuntimeStartCompleted" in kinds


# ===== 2D.3 — update / remove =====


def test_update_calls_driver_update(driver, registry, events) -> None:
    """update() delegates to driver.update_runtime."""
    import asyncio
    from app.services.runtime_manager import RuntimeManager

    mgr = RuntimeManager(registry=registry, driver=driver, events=events)
    asyncio.run(mgr.install("kokoro-82m"))
    asyncio.run(mgr.update("kokoro-82m"))
    assert "kokoro-82m" in driver.update_calls


def test_remove_clears_cache(driver, registry, events) -> None:
    """remove() calls driver.remove_runtime and clears the cache."""
    import asyncio
    from app.services.runtime_manager import RuntimeManager

    mgr = RuntimeManager(registry=registry, driver=driver, events=events)
    asyncio.run(mgr.install("kokoro-82m"))
    assert mgr.get_cached_instance("kokoro-82m") is not None
    asyncio.run(mgr.remove("kokoro-82m"))
    assert mgr.get_cached_instance("kokoro-82m") is None


def test_remove_publishes_event(driver, registry, events) -> None:
    """remove() publishes remove_completed."""
    import asyncio
    from app.services.runtime_manager import RuntimeManager

    seen: List[RuntimeEvent] = []
    events.subscribe(lambda e: seen.append(e))

    mgr = RuntimeManager(registry=registry, driver=driver, events=events)
    asyncio.run(mgr.install("kokoro-82m"))
    seen.clear()
    asyncio.run(mgr.remove("kokoro-82m"))
    kinds = [type(e).__name__ for e in seen]
    assert "RuntimeRemoveCompleted" in kinds


# ===== Resolve() uses the cache =====


def test_resolve_returns_cached_active_instance(driver, registry, events) -> None:
    """resolve() returns the cached instance when the runtime
    is installed and active. The synthetic-instance path (2B)
    is replaced by the cached-instance path (2D)."""
    import asyncio
    from app.services.runtime_manager import RuntimeManager

    mgr = RuntimeManager(registry=registry, driver=driver, events=events)
    asyncio.run(mgr.install("kokoro-82m"))
    asyncio.run(mgr.start("kokoro-82m"))
    res = mgr.resolve("kokoro-base")
    assert res is not None
    # The cached instance is the resolved instance, not a synthetic.
    assert res.instance.state == RuntimeState.ACTIVE
    # The endpoint is derived from the cached instance.
    assert res.endpoint == "http://localhost:8000"


def test_resolve_returns_none_when_runtime_not_installed(driver, registry, events) -> None:
    """resolve() returns None when the runtime is not in the
    cache (i.e. not yet installed). The bridge falls through to
    the in-process path."""
    from app.services.runtime_manager import RuntimeManager
    mgr = RuntimeManager(registry=registry, driver=driver, events=events)
    assert mgr.resolve("kokoro-base") is None


# ===== status() reads from cache when present =====


def test_status_reads_from_cache_without_calling_driver(driver, registry, events) -> None:
    """status() returns the cached instance without calling the
    driver (the cache is the manager's view of the world)."""
    import asyncio
    from app.services.runtime_manager import RuntimeManager

    mgr = RuntimeManager(registry=registry, driver=driver, events=events)
    asyncio.run(mgr.install("kokoro-82m"))
    driver.status_calls.clear()
    inst = asyncio.run(mgr.status("kokoro-82m"))
    assert inst.state == RuntimeState.INSTALLED
    # The driver was NOT called for status; the cache served the
    # request.
    assert "kokoro-82m" not in driver.status_calls
