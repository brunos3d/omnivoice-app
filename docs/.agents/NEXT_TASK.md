# NEXT TASK

> Exactly one highest-priority task — the execution queue head. When this task is done, move
> it to the execution ledger and promote the next item from [`ROADMAP/BACKLOG.md`](ROADMAP/BACKLOG.md).

**As of:** 2026-06-07

## Task: Phase 2 Sub-phase 2A — Foundations (RuntimeDescriptor, RuntimeRegistry, RuntimeManager, RuntimeDriver protocol, RuntimeInstance, RuntimeEventBus)

- **Priority:** P0. Phase 2 implementation may now begin.
- **Status:** **Ready to start.** ADR-0016 (Accepted) + ADR-0017
  (Accepted) are the architectural baseline. Architecture review
  passed (0 blocking issues; non-blocking suggestions applied).
- **Architecture review result:** ACCEPT.
  - ADR-0017 package: architecturally sound, internally consistent,
    Constitution-aligned, domain integrity preserved.
  - Non-blocking suggestions applied:
    1. **Runtime Persistence** — added as a future ADR
       ([`OPEN_DECISIONS.md` Decision 12](OPEN_DECISIONS.md)). Not
       blocking.
    2. **ADR_INDEX / IMPLEMENTATION_STATUS consistency** — ADR-0017
       status flipped from `Proposed` to `Accepted`; implementation
       status is `APPROVED` (architecture approved, no code yet),
       consistent with the ADR-0016 pattern.
- **Sub-phase 2A plan** (TDD per task, from
  [`SPECS/FEATURES/runtime-services-implementation/TASKS.md`](SPECS/FEATURES/runtime-services-implementation/TASKS.md) §2A):

  | Task | Component | File | Test |
  |---|---|---|---|
  | 2A.1 | `RuntimeDescriptor` Pydantic model | `backend/app/services/runtime_types.py` | `tests/test_runtime_descriptor.py` |
  | 2A.2 | `RuntimeInstance` frozen dataclass | `backend/app/services/runtime_instance.py` | `tests/test_runtime_instance.py` |
  | 2A.3 | `HealthReport` and `Metrics` frozen dataclasses | `backend/app/services/runtime_types.py` | `tests/test_runtime_health.py` |
  | 2A.4 | `RuntimeDriverError` hierarchy (8 subclasses) | `backend/app/services/runtime_errors.py` | `tests/test_runtime_errors.py` |
  | 2A.5 | `RuntimeDriver` Protocol (10 operations) | `backend/app/services/runtime_driver.py` | `tests/test_runtime_driver_protocol.py` |
  | 2A.6 | `RuntimeRegistryLoader` (file-based discovery + indexes) | `backend/app/services/runtime_registry.py` | `tests/test_runtime_registry.py` |
  | 2A.7 | `RuntimeEventBus` adapter (publishes to `app.core.events`) | `backend/app/services/runtime_events.py` | `tests/test_runtime_events.py` |
  | 2A.8 | `RuntimeManager` skeleton (orchestration only) | `backend/app/services/runtime_manager.py` | `tests/test_runtime_manager.py` |
  | 2A.9 | Update `IMPLEMENTATION_STATUS.md` (2A components IN_PROGRESS) | `docs/.agents/IMPLEMENTATION_STATUS.md` | cross-link check |
  | 2A.10 | `PeakVoxRuntime` integration with `RuntimeManager.resolve` | `backend/app/services/runtime.py` | `tests/test_runtime_routing_phase2.py` |

- **Definition of done — Sub-phase 2A:**
  - All 10 tasks complete; tests green.
  - `RuntimeManager` orchestrates; `RuntimeDriver` protocol is the
    only seam.
  - No new API endpoints yet.
  - No `runtime-registry/` directory created (the registry loader
    reads from a configured path; the path may be empty).
  - Existing in-process model execution **continues to work
    unchanged** when `RuntimeManager` is not wired (regression).

- **Sub-phases 2B, 2C, 2D** (sequenced behind 2A, not in flight):
  - **2B** — `DockerRuntimeDriver` + `lint_no_docker_outside_driver.py`
  - **2C** — `HTTPTransport` + `KokoroAdapter` `KOKORO_RUNTIME_URL` path
  - **2D** — CE operations (install/activate/update/remove) +
    `runtime-registry/` with Kokoro descriptor

- **Provider-validation status (unchanged):** Kokoro G5 ✅. Fish
  Audio S2 Pro still blocked on hardware. OmniVoice Base E2E
  audio test would be nice; no GPU in CI.
- **Cloud readiness gate:** still OPEN. ADR-0017 is the gateway
  to CE hardening and Cloud architecture planning (the
  `KubernetesRuntimeDriver` lands as Decision 11's separate ADR).
- **Next:** begin sub-phase 2A.

---

**Related:** [`ACTIVE_WORK.md`](ACTIVE_WORK.md) · [`ROADMAP/CURRENT_PHASE.md`](ROADMAP/CURRENT_PHASE.md) ·
[`docs/.agents/SPECS/FEATURES/runtime-services-implementation/`](SPECS/FEATURES/runtime-services-implementation/) ·
[`docs/.agents/DECISIONS/adr-0017-runtime-services-implementation.md`](DECISIONS/adr-0017-runtime-services-implementation.md) ·
[`docs/.agents/DECISIONS/adr-0016-models-as-runtime-services.md`](DECISIONS/adr-0016-models-as-runtime-services.md)
