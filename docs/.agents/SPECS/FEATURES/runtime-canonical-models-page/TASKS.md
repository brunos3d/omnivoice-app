# TASKS — Runtime-Canonical Models Page

> **Companion to:** [`SPEC.md`](./SPEC.md) · [`DESIGN.md`](./DESIGN.md)
> **Date:** 2026-06-08
>
> Each task is TDD-shaped: it states the test surface (manual or
> automated) before the implementation. Tasks are ordered so each
> lands a runnable, validating step.

---

## T0. Pre-implementation terminal validation

**Goal:** confirm the backend already exposes what the SPEC needs.

Steps:
1. `docker compose ps` — confirm `peakvox-backend` is up.
2. `curl -s http://localhost:8000/api/v1/models/with-runtimes | jq`
   — capture the JSON; verify it returns at least 4 cards
   (kokoro-base + 3 others) and the Kokoro card has
   `runtimes: [{...}]` while the others have `runtimes: []`
   (or are filtered out — see SPEC §8 R1).
3. `curl -s http://localhost:8000/api/v1/runtimes | jq` — verify
   the runtime registry surface.
4. `curl -s http://localhost:8000/api/v1/runtimes/kokoro-82m/state | jq`
   — capture the state shape.

Exit criteria: JSON captured, models with/without runtimes
identified, scope confirmed.

## T1. Extract components

**Goal:** move inline sections to testable components.

Files:
- `frontend/src/components/models/RuntimeSection.tsx` (new)
- `frontend/src/components/models/ModelSection.tsx` (new)
- `frontend/src/components/models/OperationsRow.tsx` (new)
- `frontend/src/components/models/NotMigratedEmptyState.tsx` (new)
- `frontend/src/components/models/ModelRow.tsx` (new — extract from
  the existing inline component)

Test surface: each new component renders the expected tree for a
hand-built fixture. (Manual visual check in T7 covers this; no
test framework is currently configured in the project — see
VALIDATION.md.)

Exit criteria: components compile (`tsc --noEmit`); page imports
the new components; visually identical to before.

## T2. Remove duplicated lifecycle surface

**Goal:** delete the legacy `Lifecycle` block.

Files:
- `frontend/src/app/models/page.tsx` — remove lines 23, 64-66, 382-397,
  513-539 (import, helpers, JSX block, component).

Test surface:
- `tsc --noEmit` passes.
- `grep` the page for `useModelLifecycleAction` — must return 0.
- `grep` the page for `ActionButton` — must return 0.
- `grep` the page for `Lifecycle` (within JSX) — must return 0.

Exit criteria: legacy block gone; no type or lint regressions.

## T3. Expand Runtime Section fields

**Goal:** display the full descriptor + state inside the Runtime
section.

Add to `RuntimeSection`:
- Identity row: `repository:tag` + `digest` (from `image.digest`).
- Endpoint: from `state.endpoint` (or `(no endpoint yet)` if null).
- State badge + `RUNTIME_PHASE_LABEL[phase]`.
- State metadata: `started_at`, `last_health_at`, `health_state`
  (only when present).
- Service contract: `protocol / port / health / ready / generate /
  build / metadata`.
- Requirements: `gpu / min_vram_gb / cpu_cores / memory_gb /
  edition[]`.
- Capabilities chips (from `runtime.capabilities[]`).
- `OperationsRow` (single canonical surface).

Test surface: visual check in T7.

Exit criteria: Runtime Section renders all fields for Kokoro-82m
in the descriptor file; fields are hidden when null.

## T4. Not-Migrated empty state

**Goal:** explicit `Runtime Not Migrated` label and hint.

Files:
- `NotMigratedEmptyState.tsx` — props `{ modelName: string }`,
  renders the label and a hint derived from a per-model migration
  phase table.

Phase table (in component file):
```
OmniVoice Base                  → Phase 6
OmniVoice Singing + Emotion     → Phase 6
Fish Audio S2 Pro               → Deferred (hardware)
F5-TTS                          → Phase 4
XTTS                            → Future
OpenVoice                       → Future
default                         → Future
```

Test surface: visual check in T7 — click `OmniVoice Base`, see
the explicit label.

Exit criteria: every model with no runtime renders the empty
state with the correct phase hint.

## T5. Drop legacy `useModels()` fallback (conditional)

**Goal:** keep the page rendered from a single source of truth.

Pre-condition: T0 confirmed `/models/with-runtimes` returns the
catalog model even when the runtime list is empty.

Files:
- `frontend/src/app/models/page.tsx` — remove the `useModels()`
  call (line 270 in the current file) and the
  `composedCards.map(...).runtimes[0]` derivation. Use the
  composed card's `model` field directly.

If T0 reveals the endpoint filters: do NOT remove the legacy
call; update SPEC §8 R1 and add a comment in the page explaining
the fallback is required.

Test surface: visual check that all four models still render.

Exit criteria: a single data source on the page (or a documented
fallback).

## T6. Terminal post-implementation validation

**Goal:** confirm no regressions in data or types.

Steps:
1. `cd frontend && npm run typecheck` — must pass.
2. `cd frontend && npm run lint` — must pass.
3. Re-run the three `curl` commands from T0 — must return the
   same shapes (no backend change should be visible).
4. Restart `scripts/start-dev.sh` and tail backend logs while
   loading `/models` — must show no errors.
5. `docker compose ps` — services still healthy.

Exit criteria: clean green terminal output, identical backend
shapes, no errors in logs.

## T7. Chrome DevTools visual validation

**Goal:** confirm the rendered UI matches the spec.

Steps (using Chrome DevTools MCP):
1. Open `http://localhost:3000/models`.
2. Click `Kokoro 82M` → screenshot the right panel.
3. Click `OmniVoice Base` → screenshot the right panel.
4. Click `Fish Audio S2 Pro` → screenshot the right panel.
5. Open the Network panel and confirm only one
   `GET /api/v1/models/with-runtimes` request fires on initial
   load, and one
   `GET /api/v1/runtimes/kokoro-82m/state` polls every ~10s when
   Kokoro is selected.
6. Take a "before/after" composite: show the right panel with
   the legacy Lifecycle block (sketched in the audit report) vs
   the new single Runtime section.

Exit criteria: screenshots saved to
`docs/.agents/SPECS/FEATURES/runtime-canonical-models-page/audits/screenshots/`;
visible in the audit report.

## T8. Audits and documentation updates

**Goal:** capture the change in the project documentation.

Files:
- `docs/.agents/SPECS/FEATURES/runtime-canonical-models-page/audits/models-page-canonical-control-surface.md`
  — narrative audit with before/after screenshots.
- `docs/.agents/VALIDATION/AUDITS/frontend-architecture-compliance-report.md`
  — append a section noting the duplicated control surface is
  resolved.
- `docs/.agents/IMPLEMENTATION_STATUS.md` — mark this task as
  complete in the relevant phase.
- `docs/.agents/CURRENT_CONTEXT.md` — refresh the date stamp and
  summarize the change.
- `docs/.agents/ACTIVE_WORK.md` — move this work from "in flight"
  to "recently completed".
- `docs/.agents/NEXT_TASK.md` — promote the next P0 item.

Exit criteria: every state file is consistent.

## T9. STATUS update

**Goal:** mark this feature `IMPLEMENTED` (or `VALIDATED` once
T7 passes).

File:
- `docs/.agents/SPECS/FEATURES/runtime-canonical-models-page/STATUS.md`
  — set status.

Exit criteria: STATUS.md reflects the final state.

---

## TDD Discipline Note

The project does not currently have a frontend test framework
configured (no Jest/Vitest/Playwright in `frontend/package.json`).
The validation strategy in this task list is therefore
**terminal-first + manual visual + document-traceable**, per
the project's frontend validation policy in `frontend/AGENTS.md`
and the project AGENTS.md. Adding a test framework is a
separate, deferred decision.
