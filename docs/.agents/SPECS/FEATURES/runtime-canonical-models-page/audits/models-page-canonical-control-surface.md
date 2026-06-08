# Audit — Runtime-Canonical Models Page

> **Date:** 2026-06-08
> **Scope:** Resolve the duplicated lifecycle control surface and
> establish the Runtime Section as the single canonical owner of
> model lifecycle.
> **Spec:** [`../SPEC.md`](../SPEC.md) ·
> [`../DESIGN.md`](../DESIGN.md) ·
> [`../TASKS.md`](../TASKS.md)
> **Validator:** Bruno + chrome-devtools MCP

---

## 1. Problem (before)

The Models page rendered **two** lifecycle action surfaces in the
right-side context panel:

1. **Runtime Section** (canonical, runtime-aware)
   `Install / Start / Stop / Update / Remove`
2. **Lifecycle Section** (legacy, model-aware)
   `Install / Update / Remove / Activate / Deactivate`

Both eventually delegated to `RuntimeManager.install()` and could
disagree. Models without a runtime descriptor showed a generic
empty state instead of an explicit "Runtime Not Migrated" label,
making the architecture's separation of catalog from runtime
invisible to the user.

Evidence (pre-refactor):
- `frontend/src/app/models/page.tsx:382-397` — legacy Lifecycle block
- `frontend/src/app/models/page.tsx:513-539` — `ActionButton` component
- `frontend/src/app/models/page.tsx:23` — `useModelLifecycleAction` import
- `frontend/src/hooks/use-models.ts:59-71` — `useModelLifecycleAction` hook

## 2. Resolution

The Models page is now a strict 3-tier composed view:

```
Model  (catalog)
  └─→  Runtime Descriptor  (runtime-registry/<id>/descriptor.json)
        └─→  Runtime State  (RuntimeManager)
```

- **Model section** is informational (description, metrics, sources,
  capabilities, languages & tags). Zero action buttons.
- **Runtime section** owns lifecycle. The single canonical control
  surface renders the `OPERATIONS_BY_PHASE` map (see
  [`../DESIGN.md`](../DESIGN.md) §6).
- **Not-Migrated empty state** is explicit: `Runtime Not Migrated`
  with a per-model migration phase hint.

The legacy `Lifecycle` block, `useModelLifecycleAction` page-level
import, `ActionButton` component, and `lifecycleLabel` helper are
deleted from this page. The hook itself is preserved in
`use-models.ts` (no other consumers; safe to leave in place).

## 3. Implementation summary

### 3.1 New files (extracted, reusable components)

| File | Purpose |
|---|---|
| `frontend/src/components/models/RuntimeSection.tsx` | Canonical control surface; renders descriptor + state + operations |
| `frontend/src/components/models/ModelSection.tsx` | Informational only; model metadata |
| `frontend/src/components/models/OperationsRow.tsx` | Pure state → button map |
| `frontend/src/components/models/NotMigratedEmptyState.tsx` | Explicit "Runtime Not Migrated" label |
| `frontend/src/components/models/ModelRow.tsx` | Catalog-only row in the left list |

### 3.2 Modified files

| File | Change |
|---|---|
| `frontend/src/app/models/page.tsx` | Slim orchestrator; composes the new components; drops `useModels()` fallback and `useModelLifecycleAction`; uses `asLegacyModel` cast helper once |
| `frontend/src/types/index.ts` | New `Composed*` types matching the on-disk descriptor shape returned by `/api/models/with-runtimes`; replaces the typed-as-`RuntimeCard[]` lie in the composed view |

### 3.3 Source-of-truth policy

The page depends on **one** query: `useModelsWithRuntimes()`. The
legacy `useModels()` call is removed (T0 terminal check confirmed
the backend returns the catalog model even when `runtimes[]` is
empty).

## 4. Terminal validation (T0 + T6)

| Check | Result |
|---|---|
| `docker compose ps` | 3 services healthy (`backend`, `minio`, `kokoro-runtime`) |
| `GET /api/models/with-runtimes` | 200, 4 cards, Kokoro has 1 runtime, others 0 |
| `GET /api/runtimes` | 200, 1 runtime registered |
| `GET /api/runtimes/kokoro-82m/state` | 200, `phase: "NotInstalled"` |
| `tsc --noEmit` | 0 errors |
| `eslint src/app/models src/components/models` | 0 errors, 0 warnings |
| All routes (`/`, `/voices`, `/models`, `/clone`, `/history`, `/settings`) | 200 |

## 5. Visual validation (T7)

### 5.1 OmniVoice Base (catalog only, no runtime)

`screenshots/omnivoice-base-not-migrated.png`

- Model section renders fully (description, Runtime/Memory/GPU/Edition
  metrics, Sources, Capabilities, Languages & tags)
- Runtime section: **`Runtime Not Migrated` — Phase 6 — OmniVoice migration**
- No legacy Lifecycle block
- No action buttons (correct — no runtime to operate on)

### 5.2 Kokoro 82M (catalog + runtime)

`screenshots/kokoro-runtime-section.png`

- Model section: same as above
- Runtime section: full descriptor rendered:
  - Identity: `peakvox/kokoro-runtime:0.1.0` + `Kokoro 82M Runtime`
  - State badge: `NotInstalled` with "Not Installed" label
  - **SERVICE**: protocol `http`, port `8000`, health/ready/generate/build/metadata paths
  - **REQUIREMENTS**: GPU `optional`, Min VRAM `0 GB`, CPU cores `1`, Memory `2 GB`, Edition `ce`
  - **CAPABILITIES**: `tts` chip
  - **Operations**: single `[Install]` button (the runtime's `NotInstalled` state)
- No legacy Lifecycle block
- Console: 0 errors, 0 warnings

### 5.3 Fish Audio S2 Pro (catalog only, no runtime)

`screenshots/fish-s2-pro-not-migrated.png`

- Runtime section: **`Runtime Not Migrated` — Deferred — hardware blocker (codec/VRAM)**
- Per-model phase hint correctly resolved

### 5.4 Network

`GET /models/with-runtimes` fires once on initial load. No
`GET /models` (legacy) call — the catalog is sourced entirely from
the composed view. `useModelsWithRuntimes` polls every 60s; the
per-runtime state is captured in the composed payload (no separate
state poll required for the current UX).

## 6. Acceptance criteria status

| AC | Status | Evidence |
|---|---|---|
| 1. Exactly one operations block in the runtime section | ✅ | `RuntimeSection.tsx` renders `OperationsRow` once |
| 2. Legacy Lifecycle block absent from DOM | ✅ | `grep` returns 0; visual confirmation across all 4 models |
| 3. "Runtime Not Migrated" label for non-migrated models | ✅ | Screenshots 5.1, 5.3 |
| 4. Full descriptor fields for migrated models | ✅ | Screenshot 5.2 (SERVICE + REQUIREMENTS + CAPABILITIES) |
| 5. Single query source (no legacy `useModels()` fallback) | ✅ | Network shows 0 legacy calls |
| 6. Backend coverage confirmed | ✅ | T0 terminal check |
| 7. Chrome DevTools visual validation | ✅ | Three screenshots, 0 console errors |
| 8. No regression in runtime state polling | ✅ | Composed view polls runtime state every 60s; no separate state poll needed for current UX |

## 7. Behavior change acknowledged

The legacy **Activate / Deactivate** buttons are removed. The
runtime's `Active` phase is the new "activated" state (the runtime
section shows `[Stop]` when active; the legacy section is gone).
This is the intended architectural change. Documented in
[`../VALIDATION.md`](../VALIDATION.md) so the change is traceable.

## 8. Future migrations (no frontend changes required)

The same UI architecture renders any new
`runtime-registry/<id>/descriptor.json` with zero code changes:

- OmniVoice Base → Phase 6 (descriptor entry pending)
- OmniVoice Singing → Phase 6
- Fish Audio S2 Pro → Deferred (hardware blocker)
- F5-TTS → Phase 4
- XTTS → Future
- OpenVoice → Future

When a new descriptor lands, the backend surfaces it via
`/api/models/with-runtimes`; the page renders it automatically.
