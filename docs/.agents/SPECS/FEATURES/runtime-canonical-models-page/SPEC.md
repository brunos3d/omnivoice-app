# SPEC — Runtime-Canonical Models Page

> **Feature:** `runtime-canonical-models-page`
> **Status:** DRAFT → APPROVED on user review
> **Owner:** Phase 3 full-stack convergence
> **Related ADRs:** ADR-0016, ADR-0017
> **Related Specs:** `models-as-runtime-services/`, `runtime-services-implementation/`
> **Date:** 2026-06-08

---

## 1. Problem

The Models page (`/models`) currently renders **two** lifecycle control
surfaces:

1. **Runtime Section** (canonical, runtime-aware):
   `Install / Start / Stop / Update / Remove` — operates on a
   `RuntimeCard`.
2. **Lifecycle Section** (legacy, model-aware):
   `Install / Update / Remove / Activate / Deactivate` — operates on
   the legacy `Model` row and ultimately invokes
   `RuntimeManager.install()` via the model adapter.

This is **UX duplication** and **architectural duplication**. Lifecycle
is a Runtime concern, not a Model concern. The two surfaces disagree
on vocabulary (Activate vs Start) and may diverge in behavior as the
Runtime Registry evolves.

In addition, models whose `runtime-registry/<id>/descriptor.json`
does not yet exist (e.g. `OmniVoice Base`, `OmniVoice Singing +
Emotion`, `Fish Audio S2 Pro`) are not explicitly labeled as "Runtime
Not Migrated" — they show a generic empty state that confuses users
about whether the model itself is unavailable.

## 2. Goal

The Models page becomes a strict **3-tier composed view** with
**exactly one** lifecycle control surface, owned exclusively by the
Runtime Section.

The canonical relationship is:

```
Model  (catalog)
  └─→  Runtime Descriptor  (runtime-registry/<id>/descriptor.json)
        └─→  Runtime State  (RuntimeManager)
```

For every model:

- **Model section** — informational only (name, provider, license,
  description, capabilities, languages, sources). No action buttons.
- **Runtime section** — when a `RuntimeCard` exists: descriptor fields
  (image, repository, tag, port, capabilities, requirements) + state
  (phase, endpoint, started_at) + canonical operations
  (`Install / Start / Stop / Update / Remove`).
- **Runtime section** — when no `RuntimeCard` exists: explicit empty
  state labeled `Runtime Not Migrated` with the migration hint.

## 3. Non-Goals

- No backend API changes (the `/models/with-runtimes` endpoint is
  already correct per R9 audit).
- No new runtime descriptors in this phase.
- No changes to TTS panel, voice library, wizard.
- No removal of `useModelLifecycleAction` from the codebase — only
  from this page (other call sites may exist; out of scope).

## 4. Source-of-Truth Policy

| Concern                | Authoritative source                          | API path                              |
|------------------------|------------------------------------------------|----------------------------------------|
| Model metadata         | Model Catalog                                  | `GET /api/v1/models/with-runtimes`     |
| Runtime descriptor     | `runtime-registry/<id>/descriptor.json`        | `GET /api/v1/models/with-runtimes`     |
| Runtime state          | `RuntimeManager` (in-process)                  | `GET /api/v1/runtimes/{id}/state`      |
| Lifecycle operations   | `RuntimeManager`                                | `POST /api/v1/runtimes/{id}/{action}`  |

The page renders from a **single query**:
`useModelsWithRuntimes()` returns composed cards. The composed
card's `model` field is the catalog entity; `runtimes[]` is the
registry augmentation; `default_runtime_id` selects the canonical
runtime.

## 5. UI Specification

### 5.1 Right-side context panel (selected model)

Reordered top-to-bottom:

1. **Header** — name, provider · id, status pill (derived from runtime
   state when present, else from catalog status).
2. **Model** (informational)
   - Description
   - Grid: Runtime substrate / Memory / GPU / Edition
   - Sources: Provider / Repository / Model page / License
   - Capabilities chips
   - Languages & tags
3. **Runtime** (informational + control surface)
   - **If a runtime exists:**
     - Image identity row: `repository:tag` + (digest if present)
     - Endpoint: `http://host:port` (from `state.endpoint`)
     - State badge: `RuntimePhase` with label
     - State metadata: `Started at`, `Last health`, `Health state`
     - Service contract: `protocol / port / health / ready / generate`
     - Requirements: `GPU / min_vram / cpu_cores / memory_gb / edition`
     - Capabilities chips (from `runtime.capabilities[]`)
     - **Operations** (single canonical surface):
       - `NotInstalled` → `[Install]`
       - `Pulling` / `Updating` / `Starting` / `Stopping` → disabled
         progress label, no buttons
       - `Installed` → `[Start] [Remove]`
       - `Active` → `[Stop] [Update] [Remove]`
       - `Stopped` / `Failed` → `[Start] [Remove]` (Failed also shows
         a small `Retry` hint linking to backend logs in VALIDATION.md
         — informational, not a button)
   - **If no runtime exists:**
     - Label: `Runtime Not Migrated`
     - Subtitle: explain the model is in the catalog but its runtime
       registry entry does not exist yet, with the planned phase from
       the Runtime-Service migration roadmap.

### 5.2 Removed sections

- **Lifecycle section** (current lines 382-397) — deleted.
- **`useModelLifecycleAction` import** (line 23) — removed from this
  file.
- **`ActionButton` component** (lines 513-539) — deleted (no other
  callers).
- **`lifecycleLabel` helper** (lines 64-66) — deleted.

### 5.3 Reuse rules

- The Runtime Section component is renamed from inline `RuntimeSection`
  to `RuntimeSection` and lifted into
  `frontend/src/components/models/RuntimeSection.tsx` so future
  pages (e.g. a future dedicated Runtimes page) can reuse it.
- The page imports it as a named component to keep `page.tsx` short.

## 6. Behavior Matrix

| Model state                  | Runtime state          | Operations visible                          |
|------------------------------|-------------------------|----------------------------------------------|
| Catalog only (no runtime)    | (none)                  | None                                         |
| Catalog + runtime, fresh     | `NotInstalled`          | Install                                      |
| Catalog + runtime, pulled    | `Installed`             | Start, Remove                                |
| Catalog + runtime, active    | `Active`                | Stop, Update, Remove                         |
| Catalog + runtime, transient | `Pulling`/`Starting`/`Stopping`/`Updating` | (none — pending indicator) |
| Catalog + runtime, failed    | `Failed`                | Remove (with hint)                           |

## 7. Acceptance Criteria

1. The Models page shows **exactly one** operations block in the
   context panel; it is inside the Runtime section.
2. The legacy `Lifecycle` block does not exist in the rendered DOM.
3. Models without a runtime descriptor display the explicit label
   `Runtime Not Migrated`.
4. Models with a runtime descriptor display all required descriptor
   fields (image, repository, tag, port, capabilities, requirements)
   in addition to state (phase, endpoint, started_at).
5. The page renders from `useModelsWithRuntimes()` only; the legacy
   `useModels()` fallback is removed (after backend coverage is
   verified by the pre-implementation terminal check).
6. Backend coverage check: `GET /api/v1/models/with-runtimes` returns
   at minimum the four models listed in the catalog
   (`omnivoice-base`, `omnivoice-singing-emotion`, `fish-s2-pro`,
   `kokoro-base`); the Kokoro card has a populated `runtimes` array;
   the other three have `runtimes: []` (or are absent) — and the
   UI shows the correct state for each.
7. Chrome DevTools visual validation: open `/models`, click each of
   the four models, confirm the right panel structure for both the
   "With runtime" and "Runtime Not Migrated" cases.
8. No regression in `/api/v1/runtimes/kokoro-82m/state` polled at
   10s interval (`useRuntimeState`).

## 8. Risks

- **R1** — If the backend `/models/with-runtimes` endpoint filters
  models without runtimes, removing the legacy `useModels()` call
  would hide three of the four models. *Mitigation:* the
  pre-implementation terminal check (criterion 6) must confirm
  backend coverage. If the endpoint does filter, the legacy call
  stays as a fallback and the design is updated.
- **R2** — Removing Activate/Deactivate buttons changes user-visible
  behavior. *Mitigation:* this is the intended architectural change
  (lifecycle is a runtime concern; the runtime's `Active` phase is
  the new "activated" state). Documented in VALIDATION.md.
- **R3** — Type drift between `RuntimeCard.descriptor` and the
  composed view. *Mitigation:* the composed view's `model` is typed
  as `Record<string, unknown>`; the page already type-casts to
  `Model`. This refactor preserves the same cast pattern, with one
  helper extracted to a typed selector for the descriptor's nested
  fields.

## 9. Validation

- **Pre-implementation (terminal):**
  - `docker compose ps` — all services up
  - `curl -s http://localhost:8000/api/v1/models/with-runtimes | jq`
    — verify composed shape
  - `curl -s http://localhost:8000/api/v1/runtimes | jq` — verify
    registry source
  - `curl -s http://localhost:8000/api/v1/runtimes/kokoro-82m/state | jq`
- **Post-implementation (terminal):**
  - `cd frontend && npm run typecheck && npm run lint`
  - Re-run the three curls above
  - Restart dev server, check backend logs for errors
- **Visual (Chrome DevTools MCP):**
  - Navigate to `/models`
  - Click `Kokoro 82M` → confirm full Runtime section
  - Click `OmniVoice Base` → confirm "Runtime Not Migrated" label
  - Take a screenshot of each for VALIDATION.md

## 10. Out-of-Scope Future Work

- TTS panel "active model" indicator should eventually be driven by
  the runtime's `Active` phase, not by the catalog's
  `activation_status` field. This requires backend changes and is
  deferred.
- A dedicated `/runtimes` page that lists all runtime registry
  entries regardless of model. Deferred.
- Migration of `OmniVoice Base` to a runtime registry entry. Deferred
  (Phase 6 of the Runtime-Service migration).
