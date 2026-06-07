# VALIDATION — Runtime Services Implementation (Phase 2 ADR)

> **How the work is proven.** SDD stage 6. Per Constitution §22, an
> Accepted ADR is not evidence of implementation; per Constitution
> §23, **architecture-validated ≠ provider-validated**. This file
> distinguishes the two for every Phase 2 sub-phase.
>
> **This ADR is architecture-only.** The validation surface below is
> what Phase 2 implementation must hit. No code, no tests, no
> validation reports exist in this phase. The reports are written
> as the sub-phases land.

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

**Result (Phase 2 implementation, per sub-phase):** not yet
measured. Each sub-phase lands its own result in
[`IMPLEMENTATION_STATUS.md`](../../../IMPLEMENTATION_STATUS.md) and
(where applicable) in
[`../../PROVIDER_VALIDATIONS/`](../../PROVIDER_VALIDATIONS/).

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
