# NEXT TASK

> Exactly one highest-priority task — the execution queue head. When this task is done, move
> it to the execution ledger and promote the next item from [`ROADMAP/BACKLOG.md`](ROADMAP/BACKLOG.md).

**As of:** 2026-06-07

> ## ⚠ PHASE 2 GUARDRAIL — RESOLVED FOR SUB-PHASE 2A
>
> **Sub-phase 2A of the Runtime-Service migration is COMPLETE
> (2026-06-07).** ADR-0016 + ADR-0017 are Accepted; 2A delivered
> 9 new modules + 9 test files (76 new tests, 0 regressions).
> The previous guardrail ("may not begin until ADR-0017 is
> Accepted") is satisfied for 2A; the next sub-phase (2B) may
> begin per the same architecture.
>
> **Sub-phase 2B is now the active work item.** 2B is the first
> sub-phase that introduces substrate-specific code
> (`DockerRuntimeDriver`); it is gated on the architecture
> review guardrail: "If any task requires activating runtimes,
> communicating with containers, performing inference routing,
> or introducing DockerRuntimeDriver behavior, stop and create
> a review checkpoint because that belongs to later phases."

## Task: Phase 2 Sub-phase 2B — DockerRuntimeDriver + lint_no_docker_outside_driver.py

- **Priority:** P0. Phase 2 implementation is in flight; 2A is
  complete; 2B is the next sub-phase.
- **Status:** **Ready to start.** Sub-phase 2A is complete
  (2026-06-07); 9 new modules + 9 test files delivered; 76 new
  tests; 401/401 pre-existing tests continue to pass; no
  regressions, no Docker integration, no Runtime Service
  communication, no model framework imports, no HTTP clients
  in the new modules.
- **Architecture review guardrail:** 2B is exactly the sub-phase
  that the guardrail was written for. Introducing
  `DockerRuntimeDriver` is gated on the architecture review.
  No code may be written for 2B until the review is passed (it
  was, in TASK 11).
- **Sub-phase 2B plan** (TDD per task, from
  [`SPECS/FEATURES/runtime-services-implementation/TASKS.md`](SPECS/FEATURES/runtime-services-implementation/TASKS.md) §2B):

  | Task | Component | File | Test |
  |---|---|---|---|
  | 2B.1 | `DockerRuntimeDriver` skeleton | `backend/app/services/drivers/__init__.py`, `…/docker_runtime_driver.py` | `tests/test_docker_runtime_driver.py` |
  | 2B.2 | `install_runtime` impl | … | idempotency, ImagePullError on 404, SubstrateError on daemon failure, default 300s timeout |
  | 2B.3 | `start_runtime` + readiness probe | … | container started; `/ready` polled at `lifecycle.health_interval_seconds`; success → `state=Active`, `health_state=Ready`; timeout → `state=Failed`, `RuntimeHealthFailed` |
  | 2B.4 | `stop_runtime`, `restart_runtime`, `update_runtime`, `remove_runtime`, `runtime_status`, `runtime_logs`, `runtime_health`, `runtime_metrics` | … | per-operation semantics from ADR-0017 §4.3; `runtime_metrics` returns `Metrics()` empty for first version |
  | 2B.5 | `scripts/lint_no_docker_outside_driver.py` | `scripts/` | AST scan: `import docker` outside `backend/app/services/drivers/` is a violation; runs in CI |
  | 2B.6 | Wire `DockerRuntimeDriver` into `RuntimeManager` | `backend/app/services/runtime_manager.py` | `tests/test_runtime_manager_with_docker.py` |
  | 2B.7 | Update `IMPLEMENTATION_STATUS.md` | `docs/.agents/IMPLEMENTATION_STATUS.md` | cross-link check |

- **Definition of done — Sub-phase 2B:**
  - `DockerRuntimeDriver` is the first concrete driver; the
    `RuntimeManager` depends on it through the `RuntimeDriver`
    protocol only.
  - The `lint_no_docker_outside_driver.py` script is in CI.
  - The Docker SDK import is confined to the driver package.
  - No `runtime-registry/` directory created (still); runtime
    descriptors are loaded from a configured path.
  - No new API endpoints yet.
  - Existing in-process model execution **continues to work
    unchanged** (regression: all 401 pre-existing tests still
    pass).

- **Sub-phases 2C, 2D** (sequenced behind 2B, not in flight):
  - **2C** — `HTTPTransport` + `KokoroAdapter` `KOKORO_RUNTIME_URL`
    path (additive; in-process fallback).
  - **2D** — CE operations (install/activate/update/remove) +
    `runtime-registry/` with Kokoro descriptor.

- **Provider-validation status (unchanged):** Kokoro G5 ✅. Fish
  Audio S2 Pro still blocked on hardware. OmniVoice Base E2E
  audio test would be nice; no GPU in CI.
- **Cloud readiness gate:** still OPEN. 2A → 2B unblocks both CE
  hardening and Cloud architecture planning (the
  `KubernetesRuntimeDriver` lands as Decision 11's separate ADR).
- **Next:** begin sub-phase 2B with strict TDD.

---

**Related:** [`ACTIVE_WORK.md`](ACTIVE_WORK.md) · [`ROADMAP/CURRENT_PHASE.md`](ROADMAP/CURRENT_PHASE.md) ·
[`docs/.agents/SPECS/FEATURES/runtime-services-implementation/`](SPECS/FEATURES/runtime-services-implementation/) ·
[`docs/.agents/DECISIONS/adr-0017-runtime-services-implementation.md`](DECISIONS/adr-0017-runtime-services-implementation.md) ·
[`docs/.agents/DECISIONS/adr-0016-models-as-runtime-services.md`](DECISIONS/adr-0016-models-as-runtime-services.md)
