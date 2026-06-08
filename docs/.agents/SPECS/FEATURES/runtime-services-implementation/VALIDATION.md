# VALIDATION — Runtime Services Implementation (Phase 2 ADR + Phase 3)

> **How the work is proven.** SDD stage 6. Per Constitution §22, an
> Accepted ADR is not evidence of implementation; per Constitution
> §23, **architecture-validated ≠ provider-validated**. This file
> distinguishes the two for every Phase 2 sub-phase and for the
> Phase 3 deliverables.
>
> **The audit cycle for Phase 3 is:** every Phase 3 task lands
> with tests; the architecture audit (re-run at Phase 3 close) is
> the invariant check; the provider-validated G6–G10 reports are
> the proof that a real model runs end-to-end through the Runtime
> Service.

---

## Tests (per sub-phase)

### Sub-phase 2A — Foundations (Descriptor, Registry, Manager, Driver protocol)

- **Architecture-validated:**
  - `tests/test_runtime_descriptor.py` — schema validation
    (required fields, id format, capability subset, image
    digest format, edition subset, round-trip).
  - `tests/test_runtime_instance.py` — state enum, frozen
    `image_identity`.
  - `tests/test_runtime_health.py` — liveness / readiness enums.
  - `tests/test_runtime_errors.py` — `RuntimeDriverError`
    subclasses, `runtime_id` and `message` fields.
  - `tests/test_runtime_driver_protocol.py` — structural
    conformance check; a `MockRuntimeDriver` conforms; a
    `BadRuntimeDriver` does not.
  - `tests/test_runtime_registry.py` — walk + parse + index;
    malformed descriptors logged and excluded; path traversal
    rejected; empty registry is valid.
  - `tests/test_runtime_events.py` — events emitted at the
    canonical names; frozen dataclasses.
  - `tests/test_runtime_manager.py` — `resolve`, `install`,
    `update`, `remove`, `activate`, `deactivate`, `status`,
    `logs`, `health`, `metrics`; concurrent first requests
    serialize on the in-process lock; the manager never
    imports Docker (lint check enforced in 2B).
  - `tests/test_runtime_routing_phase2.py` —
    `PeakVoxRuntime.generate` calls `RuntimeManager.resolve`
    before invoking the adapter; the existing in-process path
    remains the default.

- **Provider-validated:** Not applicable (no model migrated in 2A).

- **No regression:** existing 374+ backend tests stay green; the
  default path (no `RuntimeManager` configured) continues to
  work.

### Sub-phase 2B — First driver (Docker)

- **Architecture-validated:**
  - `tests/test_docker_runtime_driver.py` — install / start /
    stop / status / health against a mocked `docker.DockerClient`;
    pull-by-digest, pull-by-tag; idempotency;
    `ImagePullError` on registry 404;
    `SubstrateError` on Docker daemon failure;
    `RuntimeHealthFailed` on `/ready` timeout;
    `RuntimeRequirementsNotMet` on GPU-required + no-GPU.
  - `tests/test_lint_no_docker_outside_driver.py` — AST scan
    bans `import docker` outside the driver package; the
    script exits 0 on clean tree, 1 on violation.
  - `tests/test_runtime_manager_with_docker.py` — the manager
    wires the driver through the protocol; install + start
    lazy path works.

- **Provider-validated:** Not applicable (no model migrated in 2B).
  The driver is exercised against a mocked Docker daemon, not a
  real image.

- **No regression:** existing tests stay green; the
  `lint_no_docker_outside_driver.py` script is wired into CI.

### Sub-phase 2C — Service contract + KokoroAdapter integration

- **Architecture-validated:**
  - `tests/test_http_transport.py` — `HTTPTransport` against a
    mocked HTTP server; retry policy; streaming;
    `HTTPTransportError` mapping.
  - `tests/test_kokoro_runtime_adapter.py` — `KokoroAdapter`
    routes through the runtime when `KOKORO_RUNTIME_URL` is
    set; falls back in-process when unset; capability / language
    / tag / realization / build-strategy surface is unchanged.

- **Provider-validated:**
  - `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-runtime-validation-report.md`
    — real audio generated E2E through `peakvox/kokoro-runtime`
    via the new routing path. (Gated; not in default CI lane.)

- **No regression:** existing Kokoro G5 validation continues to
  pass via the in-process path; the runtime path is additive.

### Sub-phase 2D — CE operations

- **Architecture-validated:**
  - `tests/test_runtime_manager_install.py` /
    `…_activate.py` / `…_deactivate.py` / `…_update.py` /
    `…_remove.py` — orchestrator flows; events emitted at
    every transition.
  - `tests/test_runtime_manager_cli_skeleton.py` — the four
    operations are callable from a Python REPL.
  - `tests/test_runtime_registry_kokoro_descriptor.py` — the
    Kokoro descriptor parses cleanly; binds to `kokoro-base`
    with `is_default = true`, `priority = 100`,
    `metadata.edition` includes `ce`.

- **Provider-validated:** A second provider-validation report at
  `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-runtime-ce-operations-report.md`
  — a CE install (`docker compose up`) with the runtime
  installed, activated, used to generate audio, updated to a
  newer image, and removed. (Gated; not in default CI lane.)

- **No regression:** existing 374+ backend tests stay green; the
  in-process fallback still works after the operations are
  wired.

---

## Commands

```bash
# TDD: full backend test suite (per sub-phase)
docker compose run --rm backend bash -c "python -m pytest tests/ -q"

# Architecture compliance (after 2B)
python scripts/lint_no_docker_outside_driver.py

# Frontend (where applicable)
cd frontend && pnpm lint && pnpm typecheck && pnpm test

# Cross-link resolution (visual check)
rg -n "\.md\)" docs/.agents/

# E2E with real runtime (gated)
docker compose up -d peakvox-kokoro-runtime
KOKORO_RUNTIME_URL=http://localhost:8000 docker compose run --rm \
  backend bash -c "python -m pytest tests/test_kokoro_e2e_runtime.py -q"
```

---

## Result (this phase — the ADR)

**Pass criteria (this phase):**

- ADR-0017 is **Accepted**.
- All 5 spec files exist in the feature folder.
- All 10 deliverables (RuntimeDescriptor, RuntimeRegistry,
  RuntimeManager, RuntimeDriver, DockerRuntimeDriver, Service
  Contract, Runtime Routing, Kokoro Migration, CE operations,
  Cloud operations) are answered as architectural specifications.
- The 5 deferred open questions from `OPEN_DECISIONS.md`
  Decision 10 are resolved as **accepted architecture**; the
  decision is marked RESOLVED.
- `IMPLEMENTATION_STATUS.md` records ADR-0017 as **APPROVED**
  (per Constitution §22, not IMPLEMENTED).
- No code, no migrations, no `runtime-registry/` directory, no
  `RuntimeManager` class, no `RuntimeDriver` class, no
  `RuntimeDescriptor` class, no new API endpoints, no Docker
  integration, no Kokoro migration code. All deferred to
  Phase 2 implementation sub-phases (2A-2D).

**Result (Phase 2 implementation, per sub-phase):** measured.
Each sub-phase landed its own result in
[`IMPLEMENTATION_STATUS.md`](../../../IMPLEMENTATION_STATUS.md) and
(where applicable) in
[`../../PROVIDER_VALIDATIONS/`](../../PROVIDER_VALIDATIONS/).
The 374→499 test count progression is recorded; 2A+2B+2C+2D are
IMPLEMENTED.

---

## Phase 3 — Validation surface

Phase 3 is **provider-validated**, not merely architecture-
validated. The test surface below is what Phase 3 must hit, and
the **G6–G10 reports** are the only statements that a real
runtime service runs end-to-end.

### Phase 3 DoD (R5) — backend without Kokoro

The strongest architectural proof is the test below. **It is the
gate for closing Phase 3.**

```
TEST: backend starts and generates audio with kokoro REMOVED.

  1. Build a fresh backend image with `kokoro` removed from
     requirements.txt (i.e. the `kokoro` package is not installed
     in the backend image at all).
  2. Start the backend with
       RUNTIME_SERVICE_ENABLED=true
       KOKORO_RUNTIME_URL=http://peakvox-kokoro-runtime:8000
  3. Assert:
     - Backend container starts successfully.
     - Backend does not import `kokoro` (verify with
       `python -c "import kokoro"` → ModuleNotFoundError).
     - `GET /health` returns 200.
     - `POST /api/generate` with a fixture Voice returns a
       non-empty WAV.
     - The audio was produced by the runtime container
       (inspect `X-Peakvox-Request-Id` and `docker logs`).
  4. Assert (negative case):
     - When KOKORO_RUNTIME_URL is unset AND the runtime is
       unreachable, the in-process fallback path is NOT used
       (since kokoro is not installed). The request fails with
       a clear error.

RESULT: PASS / FAIL.

This is the test that proves:
  - Model != Backend
  - The backend is orchestration
  - The runtime container is the inference engine
  - The runtime container owns weights, model packages,
    inference framework, and runtime dependencies
  - The backend owns none of those
```

The regression test for the negative case is in
`backend/tests/test_backend_without_kokoro.py`. The provider-
validated report is in
`docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-g10-backend-without-kokoro-report.md`.

### Phase 3 R6 — Lazy startup

**Architecture-validated (tests):**

- `backend/tests/test_main_lifespan_no_runtime_started.py` —
  a fresh backend started with
  `RUNTIME_SERVICE_ENABLED=true` does NOT call
  `driver.start_runtime` on any runtime at startup. The
  `RuntimeManager._instance_cache` is empty. `docker ps` shows
  zero `peakvox-*` containers.
- `backend/tests/test_resolve_triggers_activation.py` — the
  first `RuntimeManager.resolve(model_id)` call activates the
  runtime; subsequent calls reuse the cached instance.

**Provider-validated:**

- `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-g6-runtime-validation-report.md`
  records the first-`resolve()`-triggers-`start_runtime`
  observation.

### Phase 3 R7 — Idle reaper

**Architecture-validated (tests):**

- `backend/tests/test_runtime_idle_reaper.py` — when an
  instance is `Active` and `now - last_request_at >
  descriptor.lifecycle.idle_timeout`, the reaper calls
  `stop_runtime`; the next `resolve()` re-activates the
  runtime; `idle_timeout = never` disables the check.
- `backend/tests/test_runtime_instance_last_request.py` —
  `touch()` updates `last_request_at`; the field is read-only
  otherwise.

**Provider-validated:**

- `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-g9-idle-reaper-report.md`
  records an actual idle-timeout observation: a runtime that
  is activated, then not touched for 15 minutes, is auto-
  stopped; the next request triggers re-activation; the event
  log records the auto-stop with a timestamp.

### Phase 3 R8 — Reference implementation pattern

**Architecture-validated (tests):**

- `backend/tests/test_runtime_descriptor_kokoro.py` — the
  Kokoro descriptor is the canonical shape. It binds to
  `kokoro-base` with `is_default = true`; it carries
  `spec.build.{entrypoint, build_context, dockerfile}`; it
  declares `spec.lifecycle.idle_timeout: "15m"`.
- `runtime-registry/kokoro-82m/tests/test_dockerfile.py` —
  the Dockerfile `EXPOSE` matches the descriptor's port; the
  `CMD` invokes `server.py`; `requirements.txt` is the entry
  in the descriptor's `spec.build`.

**Provider-validated:**

- `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-g6-runtime-validation-report.md`
  includes a "Reference shape" section that documents the
  Kokoro directory's contract, intended as the template for
  F5-TTS, XTTS, OpenVoice, Fish, and OmniVoice.

### Phase 3 G6 — runtime service contract validation

Real audio is produced end-to-end through the
`peakvox-kokoro-runtime` container:

- `runtime-registry/kokoro-82m/tests/test_docker_build.py` —
  the image builds successfully; the container starts; `/health`
  returns 200.
- `runtime-registry/kokoro-82m/tests/test_docker_generate.py` —
  `POST /v1/generate` produces a non-empty WAV for a fixture
  payload.
- `backend/tests/test_kokoro_e2e_runtime.py` — the gated E2E
  test is enabled in the docker-compose CI lane; backend
  + runtime + audio is verified.

Provider-validated report:
[`PROVIDER_VALIDATIONS/kokoro-g6-runtime-validation-report.md`](../../PROVIDER_VALIDATIONS/).

### Phase 3 G7 — performance

RTF (real-time factor), VRAM, model load time, generation
latency, p50/p95/p99. Provider-validated report:
[`PROVIDER_VALIDATIONS/kokoro-g7-performance-report.md`](../../PROVIDER_VALIDATIONS/).

### Phase 3 G8 — error recovery

Scenarios exercised: runtime container crash mid-generation,
network partition, image pull failure, OOM, timeout. Manager
behavior recorded. Provider-validated report:
[`PROVIDER_VALIDATIONS/kokoro-g8-error-recovery-report.md`](../../PROVIDER_VALIDATIONS/).

### Phase 3 G9 — idle reaper

See R7 above.

### Phase 3 G10 — backend without Kokoro

See R5 above.

### Phase 3 invariants (recap; new for Phase 3)

19. The backend boots with no runtimes active.
20. Runtimes auto-stop after `idle_timeout` of inactivity.
21. Every new runtime mirrors the Kokoro reference shape.

---

## Architecture vs provider validation (the standing distinction)

Per Constitution §23, the project tracks two distinct axes for
anything touching a model:

| Axis | Question | Evidence |
|---|---|---|
| Architecture | Can the platform represent and orchestrate the concept? | Contract / unit / integration tests; ADR accepted. |
| Provider | Does a real model run end-to-end and generate audio? | Provider validation reports with real audio output. |

ADR-0017 (this phase) is **architecture-validated** by definition
(no implementation). Each Phase 2 sub-phase is both architecture-
and provider-validated; the provider axis is gated by the
`VALIDATION/PROVIDER_VALIDATIONS/` reports.

**The two are never conflated.** "Architecture-validated" never
implies "a real model runs end-to-end"; "provider-validated" is the
only statement that a real model ran.

---

**Related:** [`TASKS.md`](./TASKS.md) · [`SPEC.md`](./SPEC.md) ·
[`DESIGN.md`](./DESIGN.md) · [`STATUS.md`](./STATUS.md) ·
[`../../VALIDATION/`](../../VALIDATION/)
