# DESIGN — Runtime-Canonical Models Page

> **Companion to:** [`SPEC.md`](./SPEC.md)
> **Date:** 2026-06-08

---

## 1. Canonical Relationship

```
Model
  └─→  Runtime Descriptor
        └─→  Runtime State
```

This diagram is rendered both in the UI (as section headers) and in
[`STATUS.md`](./STATUS.md).

- **Model** is a catalog entity. Authoritative source:
  `runtime/registry/models.py` + the in-process `BUILTIN_MODELS`
  registry loaded by `RuntimeRegistry`. Surfaced to the UI as the
  `model` field of the composed card.
- **Runtime Descriptor** is the static contract
  (`runtime-registry/<id>/descriptor.json`). It declares image,
  port, endpoints, capabilities, requirements, model_binding, and
  lifecycle policy. Authoritative source: the descriptor file
  itself. Surfaced as the `RuntimeCard.descriptor` (or as the union
  of fields lifted to `RuntimeCard` top-level: `image`, `build`,
  `service`, `capabilities`, `requirements`, `model_binding`,
  `lifecycle`).
- **Runtime State** is the operational snapshot. Authoritative
  source: `RuntimeManager`. Surfaced as `RuntimeCard.state`
  (`phase`, `endpoint`, `started_at`, `last_health_at`,
  `health_state`, `image_identity`).

## 2. Component Tree

```
ModelsPage
├── PageLayout
│   ├── PageHeader
│   ├── SummaryStats (registered / installed / available)
│   ├── Tabs (filter) + Search
│   └── ModelList
│       └── ModelRow × N         (catalog only)
└── ContextPanel (right)
    ├── Header (name, id, status)
    ├── ModelSection              (informational)
    │   ├── Description
    │   ├── Metrics grid
    │   ├── Sources
    │   ├── Capabilities chips
    │   └── Languages & tags
    └── RuntimeSection            (informational + control)
        ├── IF runtime exists:
        │   ├── Identity row (repository:tag + digest)
        │   ├── Endpoint
        │   ├── State badge + label
        │   ├── State metadata (started_at, health, ...)
        │   ├── Service contract
        │   ├── Requirements
        │   ├── Capabilities chips
        │   └── Operations
        │       ├── NotInstalled → [Install]
        │       ├── Pulling/Starting/Stopping/Updating → pending
        │       ├── Installed → [Start] [Remove]
        │       ├── Active → [Stop] [Update] [Remove]
        │       ├── Stopped → [Start] [Remove]
        │       └── Failed → [Remove] (with hint)
        └── IF no runtime:
            └── NotMigratedEmptyState
```

## 3. File Layout

```
frontend/src/
├── app/
│   └── models/
│       └── page.tsx                  (slim orchestrator)
├── components/
│   └── models/
│       ├── RuntimeSection.tsx        (NEW — extracted)
│       ├── ModelSection.tsx          (NEW — extracted)
│       ├── NotMigratedEmptyState.tsx (NEW)
│       ├── ModelRow.tsx              (NEW — extracted)
│       └── OperationsRow.tsx         (NEW — state → buttons)
├── hooks/
│   ├── use-models.ts                 (unchanged)
│   └── use-runtimes.ts               (unchanged; the page stops
│                                       calling useModelLifecycleAction)
├── lib/
│   └── api.ts                        (unchanged)
└── types/
    └── index.ts                      (unchanged)
```

The extraction keeps the page small and makes every piece unit-testable.

## 4. Data Flow

```
GET /api/v1/models/with-runtimes
  └─→ ModelsWithRuntimesResponse { models: ModelWithRuntimesCard[] }
        └─→ ModelWithRuntimesCard {
              model: ModelDescriptor,
              runtimes: RuntimeCard[],
              default_runtime_id: string | null,
            }
              └─→ RuntimeCard {
                    runtime_id, name, ...,
                    image, build, service, capabilities,
                    requirements, model_binding, lifecycle,
                    state: RuntimeStatePayload,
                  }
```

`useModelsWithRuntimes()` (in `use-runtimes.ts`) is the only data
source the page depends on for both tiers. The hook polls every
60s; for the active model, `useRuntimeState(id)` polls every 10s
to keep the state badge live.

## 5. Component Contracts

### 5.1 `RuntimeSection` (new)

```ts
interface RuntimeSectionProps {
  card: ModelWithRuntimesCard | null | undefined
  onAction: (
    runtimeId: string,
    action: RuntimeLifecycleAction
  ) => void
  actionPending: boolean
}
```

Responsibilities:
- Render the descriptor + state for the default runtime, or the
  `NotMigratedEmptyState` if `runtimes` is empty.
- Map `state.phase` to a single canonical operations surface
  (see SPEC §6).
- Never call `useModelLifecycleAction`.

### 5.2 `ModelSection` (new, informational)

```ts
interface ModelSectionProps {
  model: Model
}
```

Responsibilities:
- Render description, metrics, sources, capabilities, languages.
- Zero action buttons.

### 5.3 `OperationsRow` (new)

```ts
interface OperationsRowProps {
  phase: RuntimePhase
  pending: boolean
  onAction: (action: RuntimeLifecycleAction) => void
}
```

Pure function of `phase`. Same button set everywhere it's used.
This is the single source of truth for which buttons appear.

### 5.4 `NotMigratedEmptyState` (new)

```ts
interface NotMigratedEmptyStateProps {
  modelName: string
}
```

Renders the explicit `Runtime Not Migrated` label and the
migration hint with the phase from the Runtime-Service roadmap.

## 6. State → Operations Map

```ts
const OPERATIONS_BY_PHASE: Record<RuntimePhase, RuntimeLifecycleAction[]> = {
  NotInstalled: ["install"],
  Pulling:       [],
  Installed:     ["start", "remove"],
  Starting:      [],
  Active:        ["stop", "update", "remove"],
  Stopping:      [],
  Stopped:       ["start", "remove"],
  Failed:        ["remove"],
  Updating:      [],
}
```

`OperationsRow` reads this map and renders one button per action.
A transient phase (Pulling/Starting/Stopping/Updating) renders a
`Loader2` indicator with the human label from
`RUNTIME_PHASE_LABEL[phase]` and no buttons. This guarantees there
is **exactly one** way to render operations.

## 7. Type Safety

- `ModelWithRuntimesCard.model` is `Record<string, unknown>` at the
  type level (the composed view is structurally typed). The page
  casts it to `Model` for the informational section. The cast
  lives in exactly one place inside the page module — the
  `useMemo` that maps composed cards to `Model[]` — and is
  re-exported as the `asLegacyModel(card)` local helper used by
  the new `ModelSection` component.
- The descriptor-derived fields on `RuntimeCard` (`image`,
  `service.port`, etc.) are properly typed in
  `frontend/src/types/index.ts`. The section consumes the typed
  fields directly, no extra casts.

## 8. CSS / Layout

- The right-side context panel keeps the existing `PageLayout`
  shape. Section spacing is `space-y-6` (existing).
- The Runtime section uses an inner `rounded-md border border-border
  bg-surface-2 p-3 space-y-2` for the descriptor block and a
  separate row for operations.
- The `NotMigratedEmptyState` uses a `rounded-md border border-dashed
  border-border bg-surface-2 p-3` to visually echo the "not yet"
  state of the existing empty state.

## 9. Migration Plan (for the runtime-registry folder)

Kokoro-82m (`runtime-registry/kokoro-82m/`) is the reference
shape (R8). Future entries MUST mirror this layout:

```
runtime-registry/
└── <runtime-id>/
    ├── descriptor.json
    ├── Dockerfile
    ├── README.md
    ├── requirements.txt
    ├── server.py
    └── tests/
```

The Models page treats every `runtime-registry/<id>/` entry as
opaque. It only reads what the backend surfaces through the
composed-view endpoint. Adding a new runtime requires **zero
frontend changes** — only a new descriptor file and backend
registration.

## 10. Reuse Beyond the Models Page

Once `RuntimeSection` is extracted, the same component can be
reused by:

- A future `/runtimes` page that lists every registered runtime
  (with no catalog model on the left).
- A future "Runtimes" tab in the Voice Wizard preview surface
  (showing which runtime a voice variant will be served by).

This is the architectural payoff: lifecycle is owned in one
component, regardless of which page surfaces it.
