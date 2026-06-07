# TASKS — Runtime Services Implementation (Phase 2 ADR)

> **Task-by-task breakdown.** SDD stage 4. Uses TDD per task
> (`superpowers:test-driven-development`). The TDD shape is normative:
> every task is a failing test first, then the smallest implementation
> that makes the test pass, then refactor.
>
> **Phase 2 sub-phases:**
> - **2A — Foundations:** `RuntimeDescriptor`, `RuntimeRegistry`,
>   `RuntimeManager` skeleton, `RuntimeDriver` protocol,
>   `RuntimeInstance` dataclass, structured events.
> - **2B — First driver:** `DockerRuntimeDriver` + the
>   `lint_no_docker_outside_driver` AST check.
> - **2C — Service contract integration:** `HTTPTransport` for
>   adapters; `KokoroAdapter` adds the `KOKORO_RUNTIME_URL` path
>   (additive; in-process fallback).
> - **2D — Operations:** the CE install / activate / update /
>   remove operations; orchestrator wiring.
>
> **Do not start these tasks until ADR-0017 is Accepted** (Phase 2
> guardrail — see [`NEXT_TASK.md`](../../../NEXT_TASK.md) and
> [`ROADMAP/CURRENT_PHASE.md`](../../../ROADMAP/CURRENT_PHASE.md)).

---

## Sub-phase 2A — Foundations (Descriptor, Registry, Manager, Driver protocol)

- [ ] **2A.1** — `RuntimeDescriptor` Pydantic model in
  `backend/app/services/runtime_types.py`
  · files: `backend/app/services/runtime_types.py`
  · test (TDD): `tests/test_runtime_descriptor.py`
    - Required fields enforced; missing fields rejected
    - `api_version = "peakvox.io/v1"` and `kind = "Runtime"` enforced
    - `metadata.id` matches DNS-label rules (≤ 63 chars, lowercase,
      `[a-z0-9-.]`)
    - `spec.capabilities` rejected when it contains an entry not in
      the bound model's `ModelCapabilities` (ADR-0003)
    - `spec.requirements.edition` must be a subset of
      `metadata.edition`
    - `spec.image.digest`, when present, must be a valid
      `sha256:[0-9a-f]{64}`
    - Round-trip: a known-good YAML deserializes to the expected
      shape and re-serializes identically

- [ ] **2A.2** — `RuntimeInstance` frozen dataclass in
  `backend/app/services/runtime_instance.py`
  · files: `backend/app/services/runtime_instance.py`
  · test: `tests/test_runtime_instance.py`
    - Field types enforced (state, host, port, image_identity,
      started_at, last_health_at, health_state)
    - State enum: `Installed | Starting | Active | Stopping |
      Stopped | Failed | Removed`
    - `image_identity` is a frozen nested object
      `(repository, tag, digest)`

- [ ] **2A.3** — `HealthReport` and `Metrics` frozen dataclasses in
  `backend/app/services/runtime_types.py`
  · files: `backend/app/services/runtime_types.py`
  · test: `tests/test_runtime_health.py`
    - Liveness enum: `Alive | Dead`
    - Readiness enum: `Ready | NotReady | Unknown`
    - `Metrics` accepts an empty payload (Phase 2 may return
      empty for the first version)

- [ ] **2A.4** — `RuntimeDriverError` hierarchy in
  `backend/app/services/runtime_errors.py`
  · files: `backend/app/services/runtime_errors.py`
  · test: `tests/test_runtime_errors.py`
    - Subclasses: `RuntimeNotFound`, `ImagePullError`,
      `SubstrateError`, `RuntimeAlreadyExists`, `RuntimeNotActive`,
      `TimeoutError`, `RuntimeRequirementsNotMet`,
      `RuntimeHealthFailed`
    - All inherit from `RuntimeDriverError`
    - Each carries a `runtime_id` and a human-readable `message`

- [ ] **2A.5** — `RuntimeDriver` Protocol in
  `backend/app/services/runtime_driver.py`
  · files: `backend/app/services/runtime_driver.py`
  · test: `tests/test_runtime_driver_protocol.py`
    - The 10 normative methods are declared with the canonical
      signatures (per ADR-0017 DESIGN §4.2)
    - A `MockRuntimeDriver` test class is used to assert structural
      conformance (`runtime_checkable`)
    - A `BadRuntimeDriver` test class missing one method is
      rejected at protocol-check time

- [ ] **2A.6** — `RuntimeRegistryLoader` in
  `backend/app/services/runtime_registry.py`
  · files: `backend/app/services/runtime_registry.py`
  · test: `tests/test_runtime_registry.py`
    - Walks `<registry_root>/<id>/runtime.yaml` and parses each
      descriptor
    - Malformed descriptors are logged and excluded; one bad
      descriptor does not block the rest
    - Indexes built: `id → descriptor`, `model_id → [id]`,
      `capability → [id]`
    - `get`, `list`, `list_for_model`, `list_for_capability` all
      return expected shapes
    - Empty registry is a valid case (returns empty lists)
    - Path traversal (e.g. a descriptor with `..` in `metadata.id`)
      is rejected

- [ ] **2A.7** — `RuntimeEventBus` adapter that publishes to the
  existing `app.core.events` channel
  · files: `backend/app/services/runtime_events.py`
  · test: `tests/test_runtime_events.py`
    - Events emitted: `runtime.discovered`,
      `runtime.install.{requested,completed,failed}`,
      `runtime.start.{requested,completed,failed}`,
      `runtime.stop.{requested,completed}`,
      `runtime.update.{requested,completed}`,
      `runtime.remove.{requested,completed}`,
      `runtime.health.changed`
    - Each event is a frozen dataclass with `runtime_id`,
      `timestamp`, and event-specific fields
    - The bus is read-only; subscribers cannot mutate the channel

- [ ] **2A.8** — `RuntimeManager` skeleton in
  `backend/app/services/runtime_manager.py`
  · files: `backend/app/services/runtime_manager.py`
  · test: `tests/test_runtime_manager.py`
    - `RuntimeManager(registry, driver, events)` constructor
    - `resolve(model_id, hint=None) → endpoint` selects a
      descriptor, starts the instance if needed, and returns
      the endpoint URL
    - Selection rules: edition filter → default → priority → hint
      → first match (deterministic)
    - `install(runtime_id)`, `update(runtime_id)`,
      `remove(runtime_id)`, `activate(runtime_id)`,
      `deactivate(runtime_id)`, `status(runtime_id)`,
      `logs(runtime_id)`, `health(runtime_id)`,
      `metrics(runtime_id)` are pass-throughs to the driver
    - Concurrent first requests for the same runtime serialize
      on the in-process lock; the second request reuses the
      first's instance
    - The manager never imports Docker / Kubernetes / Podman
      (lint check enforced in 2B.5)

- [ ] **2A.9** — Update `IMPLEMENTATION_STATUS.md` (add rows for
  2A components; status: IN_PROGRESS)
  · test: cross-link check; state files reference the new
    components

- [ ] **2A.10** — `PeakVoxRuntime` (`backend/app/services/runtime.py`)
  integration with `RuntimeManager.resolve`
  · files: `backend/app/services/runtime.py`
  · test: `tests/test_runtime_routing_phase2.py`
    - `PeakVoxRuntime.generate` (or its internal pipeline) calls
      `RuntimeManager.resolve(model_id)` before invoking the
      adapter
    - The adapter receives the endpoint via a new
      `endpoint` kwarg (or via the existing `params` field — to be
      decided at implementation time; not an architecture
      question)
    - The existing in-process path remains the default when
      `RuntimeManager` is not configured (regression)

**Definition of done — Sub-phase 2A:**

- All 10 tasks complete; tests green.
- `RuntimeManager` orchestrates; `RuntimeDriver` protocol is
  the only seam.
- No new API endpoints yet. No runtime-registry/ directory
  created (the registry loader reads from a configured path;
  the path may be empty).
- Existing in-process model execution **continues to work
  unchanged** when `RuntimeManager` is not wired.

---

## Sub-phase 2B — First driver (Docker)

- [ ] **2B.1** — `DockerRuntimeDriver` skeleton in
  `backend/app/services/drivers/__init__.py` +
  `…/docker_runtime_driver.py`
  · files: `backend/app/services/drivers/docker_runtime_driver.py`
  · test: `tests/test_docker_runtime_driver.py`
    - Implements the full 10-operation `RuntimeDriver` protocol
    - All substrate calls go through a thin
      `docker.DockerClient` wrapper that is dependency-injected
      (so the test can mock the Docker daemon)
    - Container name: `peakvox-runtime-<runtime_id>`
    - Labels: `peakvox.runtime.id`, `peakvox.runtime.model_id`,
      `peakvox.edition`

- [ ] **2B.2** — `install_runtime` implementation
  · test:
    - Pull-by-digest when `spec.image.digest` is present;
      pull-by-tag otherwise
    - Idempotent: re-installing the same image is a no-op and
      returns the existing instance
    - `ImagePullError` is raised on registry 404 / auth failure
    - `SubstrateError` is raised on Docker daemon failures
    - Default timeout: 300s; configurable via
      `descriptor.spec.lifecycle.start_timeout_seconds`-equivalent
      for install (not in schema; default 300s)

- [ ] **2B.3** — `start_runtime` + readiness probe
  · test:
    - Container is started with
      `descriptor.spec.service.port` mapped
    - `GET <endpoint>/ready` is polled at
      `descriptor.spec.lifecycle.health_interval_seconds` (default
      10s) until 200 or `start_timeout_seconds` (default 60s)
    - On success: `state = Active`, `health_state = Ready`
    - On timeout: `state = Failed`, `RuntimeHealthFailed`
    - `restart_policy` is passed to Docker's `--restart` flag

- [ ] **2B.4** — `stop_runtime`, `restart_runtime`, `update_runtime`,
  `remove_runtime`, `runtime_status`, `runtime_logs`,
  `runtime_health`, `runtime_metrics`
  · test:
    - `stop_runtime`: graceful then forceful after 30s
    - `restart_runtime`: stop + start
    - `update_runtime`: stop if Active, re-pull, leave in Installed
    - `remove_runtime`: stop if Active, remove container, remove
      image
    - `runtime_status`: snapshot of the current instance
    - `runtime_logs`: async iterator over Docker logs
    - `runtime_health`: probe `/health` and `/ready`
    - `runtime_metrics`: stub returning `Metrics()` (empty) for
      Phase 2

- [ ] **2B.5** — `scripts/lint_no_docker_outside_driver.py`
  · files: `scripts/lint_no_docker_outside_driver.py`
  · test: `tests/test_lint_no_docker_outside_driver.py`
    - AST scan: any `import docker` or `from docker import ...`
      outside `backend/app/services/drivers/` is a violation
    - Any `subprocess.run([..., "docker", ...])` outside the
      driver package is a violation
    - The script exits 0 on clean tree, 1 on violation
    - Wired into the test suite (runs as part of
      `pytest tests/`)

- [ ] **2B.6** — Wire `DockerRuntimeDriver` into `RuntimeManager`
  · test: `tests/test_runtime_manager_with_docker.py`
    - `RuntimeManager(registry, driver=DockerRuntimeDriver(),
      events=...)` works
    - `resolve(model_id)` triggers install + start lazily when
      the instance is not cached

- [ ] **2B.7** — Update `IMPLEMENTATION_STATUS.md` (mark 2B
  complete; INSTALLED status where applicable)

**Definition of done — Sub-phase 2B:**

- `DockerRuntimeDriver` is the first concrete driver; the
  `RuntimeManager` depends on it through the `RuntimeDriver`
  protocol only.
- The `lint_no_docker_outside_driver.py` script is in CI.
- The Docker SDK import is confined to the driver package.
- No `runtime-registry/` directory created (still); runtime
  descriptors are loaded from a configured path.
- No new API endpoints yet.
- Existing in-process model execution **continues to work
  unchanged**.

---

## Sub-phase 2C — Service contract + KokoroAdapter integration

- [ ] **2C.1** — `HTTPTransport` (generic adapter HTTP client) in
  `backend/app/services/adapter_transport/__init__.py` +
  `…/http_transport.py`
  · files: `backend/app/services/adapter_transport/http_transport.py`
  · test: `tests/test_http_transport.py`
    - `HTTPTransport(base_url, timeout=...)` constructor
    - `get(path)`, `post(path, body)`, `post_stream(path, body)`
      methods
    - Request signing: optional bearer token (env-gated;
      defaults to none in CE)
    - Retries: 3 attempts with exponential backoff (1s, 2s, 4s)
      for network errors; no retry on 4xx; 1 retry on 5xx
    - Streaming: `post_stream` returns an async iterator over
      response bytes
    - Error mapping: non-2xx responses raise
      `HTTPTransportError` with status, category, body

- [ ] **2C.2** — Wire `KokoroAdapter` to use `HTTPTransport` when
  `KOKORO_RUNTIME_URL` is set
  · files:
    `backend/app/services/model_adapters/kokoro_adapter.py`
  · test: `tests/test_kokoro_runtime_adapter.py`
    - When `KOKORO_RUNTIME_URL` is unset: behavior identical to
      Phase 1 (in-process); existing tests pass unchanged
    - When `KOKORO_RUNTIME_URL` is set: all `generate`,
      `build_variant`, `health_check` calls route through the
      runtime
    - Capability declaration, supported languages / tags,
      realization types, build strategies are unchanged (loaded
      from the in-memory descriptor, not from the runtime
      metadata endpoint — Phase 2 reads the descriptor; a
      future phase may use the runtime's metadata endpoint)

- [ ] **2C.3** — `KOKORO_RUNTIME_URL` plumbing
  · files: `backend/app/core/config.py` (or wherever settings
    live)
  · test:
    - Default: empty string (= in-process)
    - When set: routing enabled
    - No-op when Docker is unavailable (in-process fallback
      still works)

- [ ] **2C.4** — End-to-end test: peakvox backend + `peakvox/kokoro-runtime`
  container, generating audio through the runtime service
  · test: `tests/test_kokoro_e2e_runtime.py` (integration,
    gated; not in default CI lane)
  · test: `docker compose up peakvox-backend peakvox-kokoro-runtime`
  · test: `POST /generate` returns audio
  · test: in-process fallback when `KOKORO_RUNTIME_URL` is unset
    also works

- [ ] **2C.5** — Update `IMPLEMENTATION_STATUS.md`; provider
  validation report at
  `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-runtime-validation-report.md`

**Definition of done — Sub-phase 2C:**

- `KokoroAdapter` works both in-process and through the runtime
  service.
- The in-process path is the default; the runtime path is opt-in
  via `KOKORO_RUNTIME_URL`.
- A provider-validated report exists for the runtime path
  (gated, not in default CI).
- The Kokoro migration is **additive**. The in-process path is
  not removed (Phase 7 will remove it).

---

## Sub-phase 2D — CE operations

- [ ] **2D.1** — `RuntimeManager.install(runtime_id)` orchestrator
  · files: `backend/app/services/runtime_manager.py`
  · test: `tests/test_runtime_manager_install.py`
    - Reads descriptor from registry
    - Calls `driver.install_runtime`
    - Caches the `RuntimeInstance`
    - Emits `runtime.install.{requested,completed,failed}` events

- [ ] **2D.2** — `RuntimeManager.activate(runtime_id)` /
  `deactivate(runtime_id)`
  · test:
    - `activate` calls `driver.start_runtime`
    - `deactivate` calls `driver.stop_runtime`
    - State transitions are tracked in the cache
    - Events emitted

- [ ] **2D.3** — `RuntimeManager.update(runtime_id)` /
  `remove(runtime_id)`
  · test:
    - `update` is stop-if-Active + re-pull + leave Installed
    - `remove` is stop-if-Active + drop cache + drop image
    - The descriptor in the registry is **not** removed by
      `remove` (descriptors are file-managed)

- [ ] **2D.4** — Orchestrator CLI skeleton (no actual CLI yet;
  Phase 2 wires the operations but the CLI is a separate ADR
  for UX)
  · files: `scripts/runtime_manager.py` (Python entry point
  that imports `RuntimeManager` and exposes the four operations
  as a programmatic interface; the CLI is built on top of this
  in a later phase)
  · test: `tests/test_runtime_manager_cli_skeleton.py`
    - The entry point can be invoked; the four operations are
      callable from a Python REPL

- [ ] **2D.5** — `runtime-registry/` directory published with the
  Kokoro descriptor
  · files: `runtime-registry/kokoro-cpu/{runtime.yaml,
  docker-compose.yml, env.example, README.md}`
  · test: `tests/test_runtime_registry_kokoro_descriptor.py`
    - The Kokoro descriptor parses cleanly
    - The descriptor binds to `kokoro-base` (the existing model
      id) with `is_default = true` and `priority = 100`
    - The descriptor's `metadata.edition` includes `ce`

- [ ] **2D.6** — Update `IMPLEMENTATION_STATUS.md`; update
  `PROJECT_STATE.md` and `ROADMAP/CURRENT_PHASE.md` to reflect
  the operational status of Phase 2

**Definition of done — Sub-phase 2D:**

- The four CE operations (install / activate / update / remove)
  are wired through the `RuntimeManager`.
- A `runtime-registry/` directory exists at the repo root with
  at least the Kokoro descriptor published.
- The Kokoro runtime can be installed, activated, used to
  generate audio, updated, and removed — all through the
  `RuntimeManager`.
- The in-process fallback still works (regression).

---

## Verify (per sub-phase)

Each sub-phase ends with:

```bash
# TDD: full test suite green
docker compose run --rm backend bash -c "python -m pytest tests/ -q"

# Architecture compliance (after 2B)
python scripts/lint_no_docker_outside_driver.py

# Cross-link resolution (visual)
rg -n "\.md\)" docs/.agents/

# Git status
git status --short
```

## Update state files (per sub-phase)

- [ ] `IMPLEMENTATION_STATUS.md` — add new rows; update status
- [ ] `PROJECT_STATE.md` — phase progress
- [ ] `NEXT_TASK.md` — promote the next item
- [ ] `CURRENT_CONTEXT.md` — operational memory
- [ ] `ACTIVE_WORK.md` — in-flight / paused
- [ ] `HANDOFF.md` — agent-to-agent transfer notes
- [ ] `IMPLEMENTATION/EXECUTION_HISTORY/EXECUTION_LEDGER.md` —
  append entry

## Phase 2 → Phase 3 gate

When all four sub-phases are complete and provider-validated:

- The Kokoro runtime service is operational in CE.
- The `KokoroAdapter` routes through the runtime when
  `KOKORO_RUNTIME_URL` is set; falls back in-process otherwise.
- The runtime-registry/ directory is in the repo with the
  Kokoro descriptor.
- `IMPLENTATION_STATUS.md` reflects the new reality.
- `OPEN_DECISIONS.md` Decision 10 is RESOLVED (this ADR).
- `OPEN_DECISIONS.md` Decision 11 (future drivers) is updated
  with a new "Phase 3 next" pointer.
- `NEXT_TASK.md` promotes **Phase 3 — Kokoro migration as
  the reference** (which is the actual migration of the
  Kokoro *adapter*; the runtime path is built in Phase 2; the
  validation report is the Phase 3 deliverable).

---

**Related:** [`SPEC.md`](./SPEC.md) · [`DESIGN.md`](./DESIGN.md) ·
[`VALIDATION.md`](./VALIDATION.md) · [`STATUS.md`](./STATUS.md) ·
[`adr-0017-runtime-services-implementation.md`](../../../DECISIONS/adr-0017-runtime-services-implementation.md) ·
[`adr-0016-models-as-runtime-services.md`](../../../DECISIONS/adr-0016-models-as-runtime-services.md)
