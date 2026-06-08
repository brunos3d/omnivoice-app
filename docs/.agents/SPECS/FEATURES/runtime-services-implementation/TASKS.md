# TASKS — Runtime Services Implementation (Phase 2 ADR + Phase 3)

> **Task-by-task breakdown.** SDD stage 4. Uses TDD per task
> (`superpowers:test-driven-development`). The TDD shape is normative:
> every task is a failing test first, then the smallest implementation
> that makes the test pass, then refactor.
>
> **Phase 2 sub-phases (COMPLETE 2026-06-07):**
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
> **Phase 3 (IN PROGRESS 2026-06-08):** Build the first concrete
> Runtime Service (`peakvox/kokoro-runtime`); wire the runtime
> subsystem into backend startup; connect the Models page; E2E
> validation; provider-validated G6/G7/G8; backend-without-Kokoro
> DoD.
>
> **Do not start these tasks until ADR-0017 is Accepted** (Phase 2
> guardrail — see [`NEXT_TASK.md`](../../../NEXT_TASK.md) and
> [`ROADMAP/CURRENT_PHASE.md`](../../../ROADMAP/CURRENT_PHASE.md)).
> Phase 3 tasks below assume ADR-0017 is Accepted and the 8
> refinements are applied.

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

## Phase 3 — Build peakvox/kokoro-runtime, wire it, validate E2E

The Runtime Service Readiness Audit
([`AUDITS/runtime-service-readiness-audit.md`](../../../VALIDATION/AUDITS/runtime-service-readiness-audit.md))
confirmed Phase 2 produced the runtime infrastructure but did
not deliver a concrete runtime service. Phase 3 builds the first
one — `peakvox/kokoro-runtime` — and proves the full path works
end-to-end. The eight refinements (R1–R8) are applied to the
spec/design before any of these tasks begin.

Priority is **strict**: each task depends on the prior. Skipping
a task breaks the contract.

### P1 — Build `peakvox/kokoro-runtime` (the first concrete runtime service)

- [ ] **P1.1** — Author `runtime-registry/kokoro-82m/descriptor.json`
  with `spec.build` block, `spec.lifecycle.idle_timeout: "15m"`,
  and `spec.image.repository = "peakvox/kokoro-runtime"` /
  `tag = "0.1.0"`.
  · test: descriptor parses cleanly; `build.{entrypoint, build_context}`
    are required when present; `idle_timeout` is in the closed
    vocabulary; round-trip serialization is identical.
  · file: `runtime-registry/kokoro-82m/descriptor.json`,
    `backend/tests/test_runtime_descriptor_kokoro.py` (R8
    reference test).
- [ ] **P1.2** — Author `runtime-registry/kokoro-82m/requirements.txt`
  pinning the `kokoro` framework version (CPU-only).
  · file: `runtime-registry/kokoro-82m/requirements.txt`.
- [ ] **P1.3** — Author `runtime-registry/kokoro-82m/server.py`
  (FastAPI application implementing the 5-endpoint Runtime
  Service Contract; lazy-loads the Kokoro model on first
  `/v1/generate` request):
  - `GET /health` → 200 `{"status": "alive"}` (liveness only)
  - `GET /ready` → 200 `{"status": "ready"}` only when the
    model is loaded; 503 `{"status": "not_ready", "reason": "weights_loading"}`
    otherwise
  - `POST /v1/generate` → loads the model on first call; runs
    inference; returns 200 with `audio/wav` body and
    `X-Peakvox-Duration-Ms` / `X-Peakvox-Request-Id` headers
  - `POST /v1/variants/build` → returns 501 (not implemented
    in Phase 3; the descriptor's `build_strategies` surface is
    served by the in-process adapter for the duration of Phase 3)
  - `GET /v1/metadata` → returns the canonical metadata body
    (capabilities, supported languages, supported tags, etc.)
  · test: `runtime-registry/kokoro-82m/tests/test_server.py` —
    contract test: `/health`, `/ready`, `/v1/metadata` respond
    correctly; `/v1/generate` produces real audio (CI gated; uses
    a real `kokoro` install inside the test container).
- [ ] **P1.4** — Author `runtime-registry/kokoro-82m/Dockerfile`
  based on `python:3.11-slim`. Install `requirements.txt`,
  copy `server.py` to `/app/server.py`, expose
  `spec.service.port` (8000), default `CMD ["uvicorn",
  "server:app", "--host", "0.0.0.0", "--port", "8000"]`.
  · test: `runtime-registry/kokoro-82m/tests/test_dockerfile.py`
    — parses the Dockerfile; checks the `EXPOSE` matches the
    descriptor's port; checks the `ENTRYPOINT` /
    `CMD` invokes `server.py`.
- [ ] **P1.5** — Author `runtime-registry/kokoro-82m/README.md`
  with operator notes: how to build, how to run, how to
  invoke each of the 5 endpoints with `curl`, troubleshooting,
  resource requirements.
- [ ] **P1.6** — Author `runtime-registry/kokoro-82m/tests/`
  with:
  - `__init__.py`
  - `conftest.py` (test fixtures: small fixture audio; a
    `runtime` fixture that builds + starts + tears down the
    container)
  - `test_server.py` (contract tests for the 5 endpoints)
  - `test_dockerfile.py` (Dockerfile structure checks)
  - `test_docker_build.py` (CI-gated: actually builds and
    starts the image; verifies `/health` and `/ready` 200)
  - `test_docker_generate.py` (CI-gated: actually generates
    audio and asserts a non-empty WAV is returned)

**P1 Definition of done:** `cd runtime-registry/kokoro-82m
&& docker build -t peakvox/kokoro-runtime:0.1.0 . && docker run
--rm -d -p 8000:8000 peakvox/kokoro-runtime:0.1.0 && curl
http://localhost:8000/health` returns 200; `curl
http://localhost:8000/v1/metadata` returns the canonical body;
`POST /v1/generate` with a fixture payload returns a non-empty
WAV.

### P2 — Wire `RuntimeRegistry` at backend startup (gated on R3)

- [ ] **P2.1** — Add `RUNTIME_SERVICE_ENABLED: bool = False` to
  `Settings` (`backend/app/core/config.py`).
  · test: `backend/tests/test_settings_runtime_service_enabled.py`
    — default is `False`; the field is exposed in the
    `Settings` instance; env override works.
- [ ] **P2.2** — Create `backend/app/services/runtime_wiring.py`
  with `wire_runtime_services(settings) → RuntimeManager | None`
  that:
  - Returns `None` when `settings.RUNTIME_SERVICE_ENABLED = False`.
  - Otherwise constructs `RuntimeRegistryLoader`,
    `DockerRuntimeDriver`, and `RuntimeManager`; returns the
    manager.
  · test: `backend/tests/test_runtime_wiring.py` — when the
    flag is `False`, the function returns `None`; when `True`,
    it returns a manager with a populated registry and a
    DockerRuntimeDriver instance; the registry is loaded
    from `RUNTIME_REGISTRY_PATH` (already in Settings).
- [ ] **P2.3** — Hook the wiring into `main.py` lifespan:
  when the flag is `True`, call `wire_runtime_services(settings)`
  and `PeakVoxRuntime.attach_runtime_manager(manager)`; when
  `False`, do nothing (legacy behavior).
  · test: `backend/tests/test_main_lifespan_runtime_wiring.py`
    — when the flag is `False`, no `attach_runtime_manager`
    call is made (mocked); when `True`, the manager is
    attached.

**P2 Definition of done:** A backend started with
`RUNTIME_SERVICE_ENABLED=false` continues to behave as Phase 2
(no runtime subsystem). A backend started with
`RUNTIME_SERVICE_ENABLED=true` constructs the registry, the
driver, and the manager; `attach_runtime_manager` is called
once at startup; **no runtime container is started at boot**
(R6) — `docker ps` after a fresh start with the flag true
shows zero `peakvox-*` containers.

### P3 — Wire `RuntimeManager` idle reaper (R7)

- [ ] **P3.1** — Add `idle_timeout` validation to
  `RuntimeLifecycle` (closed vocabulary: `never`, `15m`, `30m`,
  `1h`, `6h`).
  · test: `backend/tests/test_runtime_lifecycle_idle_timeout.py`
    — accepted values pass; unknown values are rejected; default
    is `15m` for CE; the field is optional (defaults apply).
- [ ] **P3.2** — Add `last_request_at: datetime | None` to
  `RuntimeInstance` (frozen; updated only via the manager's
  `touch()` method).
  · test: `backend/tests/test_runtime_instance_last_request.py`
    — `touch()` updates the timestamp; the field is read-only
    otherwise.
- [ ] **P3.3** — Add `RuntimeManager.touch(runtime_id)` and
  `RuntimeManager.run_idle_reaper()` to the manager.
  `run_idle_reaper` iterates the cache, computes
  `now - last_request_at` for each `Active` instance, and calls
  `stop_runtime` when the threshold is exceeded; emits
  `runtime.idle.timeout` event.
  · test: `backend/tests/test_runtime_idle_reaper.py` — when
    no instance is idle, nothing happens; when an instance
    exceeds the timeout, `stop_runtime` is called and the event
    is emitted; `idle_timeout = never` disables the check.
- [ ] **P3.4** — Start the reaper as an asyncio background task
  in `main.py` lifespan when `RUNTIME_SERVICE_ENABLED = True`;
  cancel the task on shutdown.
  · test: integration test that the task is created on startup
    and cancelled on shutdown (mocked).

**P3 Definition of done:** A runtime that is activated, then
not touched for `idle_timeout`, is auto-stopped; the next
`resolve()` re-activates it; the event log records the
auto-stop.

### P4 — Connect Models page operations to `RuntimeManager` (R4)

- [ ] **P4.1** — Refactor `backend/app/services/model_lifecycle.py`
  to delegate to `RuntimeManager` (when attached) or to the
  legacy DB-status mock (when not attached). The current
  pure-DB behavior is the fallback; the manager path is the
  primary path.
  · test: `backend/tests/test_model_lifecycle_runtime_integration.py`
    — when the manager is attached, `install_model` calls
    `runtime_manager.install` then updates `model.status` to
    `INSTALLED` only on success; failure does not update the
    status; the legacy path is preserved when no manager is
    attached.
- [ ] **P4.2** — Update `backend/app/api/models.py` to surface
  the manager's events in the API response (best-effort).
  · test: `backend/tests/test_models_api_runtime_integration.py`
    — `POST /api/models/{id}/install` returns 202 with a
    `runtime_id` field; the response is built from the manager's
    outcome.
- [ ] **P4.3** — Document the new wiring in
  `docs/.agents/ARCHITECTURE/runtime-architecture.md`.

**P4 Definition of done:** The Models page Install / Activate /
Deactivate / Remove buttons trigger the corresponding
`RuntimeManager` operations; model status transitions are a
side-effect of runtime transitions; the legacy in-process path
is preserved when `RUNTIME_SERVICE_ENABLED = False`.

### P5 — Add `peakvox-kokoro-runtime` to `docker-compose.yml`

- [ ] **P5.1** — Add a `peakvox-kokoro-runtime` service to
  `docker-compose.yml` (depends on `backend`; uses the image
  built from `runtime-registry/kokoro-82m/Dockerfile`; exposes
  port 8000; sets `KOKORO_RUNTIME_URL` in the `backend` service
  to `http://peakvox-kokoro-runtime:8000`).
  · test: `docker compose config` validates the file.
- [ ] **P5.2** — Add `KOKORO_RUNTIME_URL=http://peakvox-kokoro-runtime:8000`
  to `.env.example`.
- [ ] **P5.3** — Add a healthcheck for `peakvox-kokoro-runtime`
  in `docker-compose.yml` that probes `/health` every 10 seconds.

**P5 Definition of done:** `docker compose up` brings up
`backend`, `peakvox-kokoro-runtime`, `minio`, `frontend`. The
runtime container is healthy. The backend can reach the
runtime over the compose network.

### P6 — Execute real E2E generation through the runtime service

- [ ] **P6.1** — Enable `tests/test_kokoro_e2e_runtime.py` in
  the docker-compose CI lane (remove the skip; the test now
  has a real `peakvox-kokoro-runtime` to talk to).
  · test: the test passes when run with
  `KOKORO_RUNTIME_URL=http://peakvox-kokoro-runtime:8000`.
- [ ] **P6.2** — Author a manual E2E script at
  `scripts/e2e_runtime_generation.sh` that:
  - Builds the Kokoro runtime image
  - Brings up the compose stack
  - Calls `POST /api/generate` with a fixture Voice
  - Asserts a non-empty WAV is returned
  - Asserts the audio was generated by the runtime
    (e.g. `X-Peakvox-Request-Id` header)

**P6 Definition of done:** End-to-end generation produces real
audio through the Runtime Service. The in-process path
remains as a fallback (`KOKORO_RUNTIME_URL` unset).

### P7 — Provider validation: G6 + G7 + G8

- [ ] **P7.1** — Update
  `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-runtime-validation-report.md`
  with real E2E data: audio sample, latency, log excerpts,
  request/response bodies.
- [ ] **P7.2** — Author
  `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-g7-performance-report.md`:
  RTF (real-time factor), VRAM, model load time, generation
  latency, p50/p95/p99.
- [ ] **P7.3** — Author
  `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-g8-error-recovery-report.md`:
  error recovery scenarios — runtime container crashes mid-
  generation, network partition, image pull failure, OOM,
  timeout. Each scenario is exercised, the outcome is
  recorded, the manager's behavior is verified.
- [ ] **P7.4** — Author
  `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-g9-idle-reaper-report.md`:
  the idle reaper is exercised; auto-stop is observed;
  re-activation after timeout is observed; event log is
  inspected.

**P7 Definition of done:** All four provider-validation
reports exist with real data. Reports are referenced from
`OPEN_DECISIONS.md` Decision 11 (future drivers) as the
"reference pattern" for F5-TTS, XTTS, OpenVoice, etc.

### P8 — Validate the backend starts without `kokoro` installed (R5)

- [ ] **P8.1** — Add a `pyproject.toml` / `requirements.txt`
  layer that distinguishes backend deps from runtime deps. The
  backend MUST NOT declare `kokoro` as a direct dependency;
  the runtime container owns it.
  · test: a CI job that builds a fresh backend image with
    `kokoro` removed from `requirements.txt`; the image
    builds successfully; the container starts successfully;
    `python -c "import sys; 'kokoro' in sys.modules"` is
    `False`.
- [ ] **P8.2** — Author a regression test at
  `backend/tests/test_backend_without_kokoro.py` that runs in
  a subprocess with the `kokoro` import blocked at the
  Python level (`sys.modules['kokoro'] = None`) and asserts
  that the backend starts and serves the Models page
  endpoints.
- [ ] **P8.3** — Document the result in
  `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-g10-backend-without-kokoro-report.md`.

**P8 Definition of done:** The backend image starts and serves
traffic with `kokoro` removed from the backend Python
environment. Voice generation succeeds through the Runtime
Service. The "Model != Backend" invariant is proven.

### P9 — Update state files

- [ ] **P9.1** — Update `IMPLEMENTATION_STATUS.md`:
  - Phase 2 ADR-0017 row flips from `IMPLEMENTED (2A+2B+2C+2D)`
    to `VALIDATED` (Phase 3 is the validation phase).
  - Phase 3 row added at status `IN_PROGRESS` → `IMPLEMENTED`
    as tasks land.
- [ ] **P9.2** — Update `PROJECT_STATE.md` and
  `ROADMAP/CURRENT_PHASE.md`: Phase 3 promoted to `IN PROGRESS`;
  Phase 4 (F5-TTS) unblocked.
- [ ] **P9.3** — Update `NEXT_TASK.md`: the next item is
  **Phase 4 — F5-TTS as Runtime Service** (mirroring the
  Kokoro reference shape per R8).
- [ ] **P9.4** — Update `ACTIVE_WORK.md` and
  `CURRENT_CONTEXT.md` with the operational memory of
  Phase 3.

**P9 Definition of done:** All state files reflect the
post-Phase-3 reality. Phase 4 has a clear next-task pointer.

---

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
