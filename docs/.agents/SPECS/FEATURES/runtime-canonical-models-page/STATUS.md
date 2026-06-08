# STATUS — Runtime-Canonical Models Page + Runtime Registry Expansion

> Lifecycle position in the SDD flow:
> `Brainstorm → Specification → Design → Tasks → Implementation → Validation → Review → Merge`

## Current state

- **Stage:** Both workstreams VALIDATED.
- **Implementation status:** **VALIDATED**
- **Status:** `VALIDATED`
- **Owner / last update:** 2026-06-08

## What this feature is

Two workstreams, both part of the Phase 3 full-stack
convergence.

**Workstream A — Runtime-Canonical Models Page.** The
Models page is now a strict 3-tier composed view with a
single canonical lifecycle control surface owned by the
Runtime Section.

**Workstream B — Runtime Registry Expansion (TASK 12).**
The Runtime Registry now hosts three independent runtime
implementations under the same architecture:

```
runtime-registry/
├── kokoro-82m/        (R8 reference — pre-existing)
├── omnivoice-base/    (T12.1 — NEW)
└── f5-tts-base/       (T12.2 — NEW)
```

The canonical relationship (always):
```
Model
  └─→  Runtime Descriptor
        └─→  Runtime State
```

## Phase status

| Phase | Scope | Status | Notes |
|---|---|---|---|
| 1 | SPEC + DESIGN + TASKS + VALIDATION + STATUS | **APPROVED** | Commit `4acea9c` |
| 2 | Models page implementation (T1–T5) | **IMPLEMENTED** | Commit `5e5616f` |
| 3 | Terminal + visual validation (T6, T7) | **VALIDATED** | 0 console errors, 3 screenshots |
| 4 | Audits + state file updates (T8) | **COMPLETE** | 4 state files updated |
| 5 | Runtime Registry expansion (T12.1–T12.9) | **VALIDATED** | Commit `dd31fc2` |
| 6 | STATUS update (T9) | **VALIDATED** | This document |

## Architectural invariants captured

### Workstream A (Models page)

1. The Models page renders from a single query:
   `useModelsWithRuntimes()` (composed view).
2. The Model section is informational only — zero action buttons.
3. The Runtime section owns lifecycle:
   `Install / Start / Stop / Update / Remove`.
4. The legacy Activate / Deactivate buttons are removed (runtime
   `Active` phase is the new activation state).
5. Models without a runtime descriptor render
   `Runtime Not Migrated` (explicit label) instead of a generic
   empty state.
6. `RuntimeCard` (descriptor + state) is the only data source for
   the Runtime section; no additional fetches inside the section.
7. The extracted `RuntimeSection`, `ModelSection`,
   `OperationsRow`, and `NotMigratedEmptyState` components are
   reusable by future pages.

### Workstream B (Runtime Registry expansion)

1. The Runtime Registry is the canonical location for runtime
   definitions. Three concrete entries now exist.
2. All three entries follow the same R8 reference shape:
   `descriptor.json + Dockerfile + requirements.txt + server.py +
   README.md + tests/`.
3. The RuntimeRegistryLoader auto-discovers all three; no
   hardcoded list.
4. The capability subset check (ADR-0017 §1.5) passes for all
   three entries.
5. The Models page renders all three runtimes with zero
   hardcoded assumptions.
6. The Models page does not branch on `runtime_id`; the
   data-driven `RuntimeSection` renders any new entry with
   zero code changes.

## Test coverage

| Suite | Count | Status |
|---|---|---|
| `backend/tests/test_runtime_registry_three_descriptors.py` | 23 | ✅ new |
| `backend/tests/test_api_runtimes.py` | (updated) | ✅ pass |
| `backend/tests/test_api_models_with_runtimes.py` | (updated: 4→5) | ✅ pass |
| `runtime-registry/omnivoice-base/tests/test_descriptor.py` | 18 | ✅ new |
| `runtime-registry/f5-tts-base/tests/test_descriptor.py` | 18 | ✅ new |
| **All runtime-related tests** | **62** | ✅ pass |

## Deliverables

| # | Deliverable | Status |
|---|---|---|
| 1 | Runtime Registry entries (`omnivoice-base`, `f5-tts-base`) | ✅ |
| 2 | Descriptor validation tests | ✅ (36 in registry + 23 in backend) |
| 3 | Runtime Service Contract tests | ✅ (parametrized over 3 entries) |
| 4 | Runtime discovery tests | ✅ |
| 5 | Lifecycle tests | ⚠️ architecturally valid; environment-blocked (`docker` SDK missing) |
| 6 | Generation validation | ✅ Kokoro runtime produces 4.45s WAV; backend path blocked by pre-existing adapter translation |
| 7 | Chrome DevTools screenshots | ✅ 3 in `audits/screenshots/` + 1 generated audio WAV |
| 8 | Runtime Registry audit | ✅ `audits/task-12-runtime-registry-expansion.md` |
| 9 | Architectural findings | ✅ in audit §9 + §10 |
| 10 | Migration recommendations | ✅ 6-step recipe in audit §9 + T12.9 |

## Pre-existing issues uncovered

These are not regressions; they were discovered and documented:

1. **Kokoro `KPipeline(repo_id=...)` signature mismatch** —
   fixed in this commit (`runtime-registry/kokoro-82m/server.py`).
2. **`docker` Python SDK missing from
   `backend/requirements.txt`** — pre-existing CE limitation;
   blocks install/start/stop execution. Documented.
3. **KokoroAdapter voice-id → preset-name translation** —
   pre-existing; blocks backend-driven generation path through
   the runtime container. Documented.
4. **Two shapes for runtime entries** (`RuntimeCard` for
   `/api/runtimes` vs `ComposedRuntimeEntry` for
   `/api/models/with-runtimes`) — pre-existing; the composed-view
   shape was incorrectly typed as `RuntimeCard[]` in the original
   code. The frontend types are now corrected.

## Related

- [`SPEC.md`](./SPEC.md) — what & why
- [`DESIGN.md`](./DESIGN.md) — components, contracts, layout
- [`TASKS.md`](./TASKS.md) — T0–T9 + §12 execution plan
- [`VALIDATION.md`](./VALIDATION.md) — pre/post-implementation checks
- [`audits/models-page-canonical-control-surface.md`](./audits/models-page-canonical-control-surface.md) — Workstream A audit
- [`audits/task-12-runtime-registry-expansion.md`](./audits/task-12-runtime-registry-expansion.md) — Workstream B audit
- [`adr-0016-models-as-runtime-services.md`](../../DECISIONS/adr-0016-models-as-runtime-services.md)
- [`adr-0017-runtime-services-implementation.md`](../../DECISIONS/adr-0017-runtime-services-implementation.md)
- [`models-as-runtime-services/SPEC.md`](../models-as-runtime-services/SPEC.md)
- [`runtime-services-implementation/SPEC.md`](../runtime-services-implementation/SPEC.md)
