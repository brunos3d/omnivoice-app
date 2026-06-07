# Current Phase

**As of:** 2026-06-07 · **Branch:** `feat/peakvox-phase-1`

## Phase: CE spine complete → Runtime-Service architecture

Phases 1–3 (including sub-phases 3.5–3.11) are **built and tested**. Kokoro provider
validation passed (G5 — real audio E2E through the Runtime, see
`docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-validation-report.md`).
The platform is a **multi-provider Universal Voice Runtime with a
substrate-implicit deployment model**.

The new direction ([ADR-0016](../DECISIONS/adr-0016-models-as-runtime-services.md),
accepted 2026-06-07) replaces the substrate-implicit model with an explicit
**Runtime-Service architecture**: Runtime Registry + Runtime Manager + Runtime
Driver + Runtime Service. 7-phase migration; Phase 1 (this) is documentation
only.

### Done in this phase

- Platform foundations (flags, vendor seams, schema-ready commercial tables).
- Model registry + canonical metadata + capability contract.
- Voice/Variant split, Runtime exclusivity, ModelAdapter contract, build lifecycle, artifact
  versioning, edition scoping.
- Voice Library 2.0 UI, Variant Dashboard, variant backfill UX.
- Kokoro provider validation (G5 passed — real audio E2E through the Runtime).
- Runtime-Service architecture (Phase 1, ADR + design docs).

### In progress

- **Runtime-Service migration — Phase 2 Sub-phase 2B (`DockerRuntimeDriver`).** TDD
  tasks in
  [`../SPECS/FEATURES/runtime-services-implementation/TASKS.md`](../SPECS/FEATURES/runtime-services-implementation/TASKS.md) §2B.

> ## ⚠ PHASE 2 IMPLEMENTATION GUARDRAIL — RESOLVED FOR SUB-PHASE 2A
>
> **Sub-phase 2A is COMPLETE (2026-06-07).** Phase 2 implementation
> may continue; the next sub-phase is 2B (`DockerRuntimeDriver`).
>
> **Current state (2026-06-07):**
> - ADR-0016 (architecture): **Accepted** (2026-06-07).
> - ADR-0017 (Phase 2 implementation architecture): **Accepted**
>   (2026-06-07). Architecture review: 0 blocking issues;
>   non-blocking suggestions applied (Runtime Persistence →
>   `OPEN_DECISIONS.md` Decision 12).
> - Sub-phase 2A (Foundations): **✅ Complete.** 9 new modules +
>   9 test files; 76 new tests; 401/401 pre-existing tests pass;
>   no Docker integration, no Runtime Service communication, no
>   model framework imports, no HTTP clients. `PeakVoxRuntime`
>   bridge is a transitional pass-through; behavior unchanged in
>   2A. See
>   [`../IMPLEMENTATION_STATUS.md` §"Phase 2A — Runtime Services
>   Foundations"](../IMPLEMENTATION_STATUS.md).
> - Sub-phase 2B (`DockerRuntimeDriver`): **ready to start**.
>   TDD tasks in
>   [`../SPECS/FEATURES/runtime-services-implementation/TASKS.md`](../SPECS/FEATURES/runtime-services-implementation/TASKS.md) §2B.
> - Sub-phases 2C, 2D: sequenced behind 2B.
>
> Sub-phase 2A ✅ done. Sub-phase 2B may begin. TDD-shaped tasks:
>
> | # | Component | File | Test |
> |---|---|---|---|
> | 2B.1 | `DockerRuntimeDriver` skeleton | `backend/app/services/drivers/docker_runtime_driver.py` | `tests/test_docker_runtime_driver.py` |
> | 2B.2 | `install_runtime` impl | … | idempotency, ImagePullError on 404, SubstrateError on daemon failure, default 300s timeout |
> | 2B.3 | `start_runtime` + readiness probe | … | container started; `/ready` polled; success → `Active`/`Ready`; timeout → `Failed`/`RuntimeHealthFailed` |
> | 2B.4 | `stop_runtime`, `restart_runtime`, `update_runtime`, `remove_runtime`, `runtime_status`, `runtime_logs`, `runtime_health`, `runtime_metrics` | … | per-operation semantics from ADR-0017 §4.3 |
> | 2B.5 | `scripts/lint_no_docker_outside_driver.py` | `scripts/` | AST scan: `import docker` outside driver pkg is a violation |
> | 2B.6 | Wire `DockerRuntimeDriver` into `RuntimeManager` | `backend/app/services/runtime_manager.py` | `tests/test_runtime_manager_with_docker.py` |
> | 2B.7 | Status updates | `docs/.agents/IMPLEMENTATION_STATUS.md` | cross-link |

### The gate before Cloud work

Cloud phases (4–10) are no longer blocked by the provider-validation gate (Kokoro
G5 passed). However, investing in Cloud before Runtime-Service Phase 2 lands
would re-couple backend to model execution. **Phase 2 first; deliberate Cloud
sequencing afterward.**

### Candidate parallel phases

- **Phase 9 — Public API harden** — can proceed in parallel with Phase 2.
- **Runtime-Service migration Phases 3–7** — sequenced behind Phase 2.

---

**Related:** [`ROADMAP.md`](../ARCHIVE/LEGACY/ROADMAP.md) · [`../NEXT_TASK.md`](../NEXT_TASK.md) ·
[`../VALIDATION/RETROSPECTIVES/`](../VALIDATION/RETROSPECTIVES/) ·
[`../SPECS/FEATURES/models-as-runtime-services/`](../SPECS/FEATURES/models-as-runtime-services/) ·
[`../DECISIONS/adr-0016-models-as-runtime-services.md`](../DECISIONS/adr-0016-models-as-runtime-services.md)
