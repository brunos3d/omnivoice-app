# STATUS — Runtime-Canonical Models Page

> Lifecycle position in the SDD flow:
> `Brainstorm → Specification → Design → Tasks → Implementation → Validation → Review → Merge`

## Current state

- **Stage:** Design approved, awaiting implementation.
- **Implementation status:** **IN_PROGRESS**
- **Status:** `IN_PROGRESS`
- **Owner / last update:** 2026-06-08

## What this feature is

The Models page becomes a strict 3-tier composed view with a
single canonical lifecycle control surface owned by the Runtime
Section.

```
Model
  └─→  Runtime Descriptor
        └─→  Runtime State
```

## Phase status

| Phase | Scope                                       | Status      | Notes |
|-------|----------------------------------------------|-------------|-------|
| 1     | SPEC + DESIGN + TASKS + VALIDATION + STATUS | **APPROVED** | This document. |
| 2     | Implementation (T1–T5)                       | IN_PROGRESS | See `TASKS.md`. |
| 3     | Terminal validation (T6)                     | PENDING     |       |
| 4     | Visual validation (T7)                       | PENDING     |       |
| 5     | Audit + state file updates (T8–T9)           | PENDING     |       |

## Architectural invariants captured

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
   reusable by future pages (a dedicated `/runtimes` page, the
   Voice Wizard, etc.).

## Related

- [`SPEC.md`](./SPEC.md) — what & why
- [`DESIGN.md`](./DESIGN.md) — components, contracts, layout
- [`TASKS.md`](./TASKS.md) — T0–T9 execution plan
- [`VALIDATION.md`](./VALIDATION.md) — pre/post-implementation checks
- [`adr-0016-models-as-runtime-services.md`](../../DECISIONS/adr-0016-models-as-runtime-services.md)
- [`adr-0017-runtime-services-implementation.md`](../../DECISIONS/adr-0017-runtime-services-implementation.md)
- [`models-as-runtime-services/SPEC.md`](../models-as-runtime-services/SPEC.md)
- [`runtime-services-implementation/SPEC.md`](../runtime-services-implementation/SPEC.md)
