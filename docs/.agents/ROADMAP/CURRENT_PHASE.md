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

- **Runtime-Service migration — Phase 2 Sub-phase 2A (Foundations).** TDD
  tasks in
  [`../SPECS/FEATURES/runtime-services-implementation/TASKS.md`](../SPECS/FEATURES/runtime-services-implementation/TASKS.md) §2A.

> ## ⚠ PHASE 2 IMPLEMENTATION GUARDRAIL — RESOLVED
>
> **ADR-0017 is Accepted (2026-06-07).** Phase 2 implementation
> may begin. The previous guardrail is no longer in force.
>
> **Current state (2026-06-07):**
> - ADR-0016 (architecture): **Accepted** (2026-06-07).
> - ADR-0017 (Phase 2 implementation architecture): **Accepted**
>   (2026-06-07). Architecture review: 0 blocking issues;
>   non-blocking suggestions applied (Runtime Persistence →
>   `OPEN_DECISIONS.md` Decision 12).
> - Sub-phase 2A (Foundations): **ready to start**. TDD tasks
>   in
>   [`../SPECS/FEATURES/runtime-services-implementation/TASKS.md`](../SPECS/FEATURES/runtime-services-implementation/TASKS.md) §2A.
> - Sub-phases 2B, 2C, 2D: sequenced behind 2A.
>
> Sub-phase 2A may begin. TDD-shaped tasks:
>
> | # | Component | File | Test |
> |---|---|---|---|
> | 2A.1 | `RuntimeDescriptor` Pydantic | `backend/app/services/runtime_types.py` | `tests/test_runtime_descriptor.py` |
> | 2A.2 | `RuntimeInstance` | `backend/app/services/runtime_instance.py` | `tests/test_runtime_instance.py` |
> | 2A.3 | `HealthReport` / `Metrics` | `backend/app/services/runtime_types.py` | `tests/test_runtime_health.py` |
> | 2A.4 | `RuntimeDriverError` hierarchy | `backend/app/services/runtime_errors.py` | `tests/test_runtime_errors.py` |
> | 2A.5 | `RuntimeDriver` Protocol | `backend/app/services/runtime_driver.py` | `tests/test_runtime_driver_protocol.py` |
> | 2A.6 | `RuntimeRegistryLoader` | `backend/app/services/runtime_registry.py` | `tests/test_runtime_registry.py` |
> | 2A.7 | `RuntimeEventBus` | `backend/app/services/runtime_events.py` | `tests/test_runtime_events.py` |
> | 2A.8 | `RuntimeManager` skeleton | `backend/app/services/runtime_manager.py` | `tests/test_runtime_manager.py` |
> | 2A.9 | Status updates | `docs/.agents/IMPLEMENTATION_STATUS.md` | cross-link |
> | 2A.10 | `PeakVoxRuntime` integration | `backend/app/services/runtime.py` | `tests/test_runtime_routing_phase2.py` |

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
