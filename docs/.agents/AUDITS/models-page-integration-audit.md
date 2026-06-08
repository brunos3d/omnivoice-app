# Models Page Backend Integration Audit (Task 2)

**Date:** 2026-06-08
**Subject:** Trace UI → API → Runtime Manager → Runtime Registry. Document what is real, mocked, stale, or disconnected.
**Status:** AUDIT COMPLETE
**Result:** The Models page is wired to the **legacy DB-status mock**, not the runtime-registry. The runtime path is built but the UI does not see it. The fix is Tasks 3-7.

---

## The full trace

### 1. UI layer (Models page)

**File:** `frontend/src/app/models/page.tsx`

The Models page calls:
- `useModels()` from `frontend/src/hooks/use-models.ts` — returns the catalog from `/api/models`.
- `useModelLifecycleAction()` — issues install/activate/etc. via `lifecycleFns[action](id)`.

**Cards:** four entries rendered today, with the **legacy status model**:
- "Registered" — never installed.
- "Installed" — DB status `inactive` (the "installed but not active" state).
- "Available" — DB status `available` (the "active" state).
- "Active" — DB status `loaded` (the "in-memory resident" state).

These states are **DB statuses** (set by `_set_status()` in `model_lifecycle.py`), not runtime states. They reflect the legacy mock, not the runtime subsystem.

**Filters:** "all" / "installed" / "available" (the catalog view's filters).

### 2. Hooks layer

**File:** `frontend/src/hooks/use-models.ts`

```ts
lifecycleFns = {
  install:   installModel,
  update:    updateModel,
  remove:    removeModel,
  activate:  activateModel,
  deactivate: deactivateModel,
}
```

Each function calls the backend; the backend's `api/models.py` handler delegates to `model_lifecycle.py` which delegates to `RuntimeManager` (when attached) or to the legacy DB-status mock (when not attached).

**Critical observation:** the `useModelLifecycleAction` hook has no knowledge of runtime state. After the action returns, it invalidates the `["models"]` query, which re-fetches `/api/models`. The UI does not subscribe to runtime state directly.

### 3. API layer

**File:** `backend/app/api/models.py`

| Endpoint | Handler | Reads from | Writes to |
|---|---|---|---|
| `GET /api/models` | `list_models` | `model_registry.list_models(edition=...)` | — |
| `GET /api/models/{id}` | `get_model` | `model_registry.get(id)` | — |
| `GET /api/models/{id}/tags` | `get_model_tags` | `tag_catalog.tags_for(...)` | — |
| `GET /api/models/{id}/status` | `get_model_status` | `model_registry.status(id)` | — |
| `POST /api/models/{id}/install` | `install` | — | `model_lifecycle.install_model` → `RuntimeManager.install` (or legacy) |
| `POST /api/models/{id}/activate` | `activate` | — | `model_lifecycle.activate_model` → `RuntimeManager.start` (or legacy) |
| `POST /api/models/{id}/deactivate` | `deactivate` | — | `model_lifecycle.deactivate_model` → `RuntimeManager.stop` (or legacy) |
| `POST /api/models/{id}/update` | `update` | — | `model_lifecycle.update_model` → `RuntimeManager.update` (or legacy) |
| `POST /api/models/{id}/remove` | `remove` | — | `model_lifecycle.remove_model` → `RuntimeManager.remove` (or legacy) |

**The list endpoint reads from `ModelRegistry` (DB-backed).** No endpoint reads from `RuntimeRegistry` (file-backed). The runtime-registry is invisible to the API.

### 4. ModelRegistry layer (DB-backed)

**File:** `backend/app/services/model_registry.py`

In-memory cache of `ModelDescriptor` (the **catalog** type, not the runtime type). Populated from the `models` table at startup by `wire_registry_from_database`. Carries status (the legacy DB-status column).

**The ModelRegistry carries:**
- `id` (e.g. `kokoro-base`)
- `name` (e.g. `Kokoro 82M`)
- `provider` (e.g. `kokoro`)
- `repo_id` (the Hugging Face repo; legacy artifact source)
- `capabilities` (from `ModelCapabilities`)
- `supported_tags` (the catalog's tag list)
- `status` (the DB column: `available`, `loaded`, `loading`, `error`, `disabled`, `inactive`, `deprecated`)
- `install_status` (legacy mock: `installed` / `not_installed`)

**The ModelRegistry does NOT carry:**
- `image.repository` / `image.tag` / `image.digest`
- `runtime_id` (the `kokoro-82m` identifier)
- `build.{entrypoint, build_context, dockerfile}`
- `service.{port, paths}`
- `lifecycle.idle_timeout`
- `host` / `port` (the runtime endpoint)
- `state` (`Active` / `Installed` / `Stopped` / `Failed`)
- `last_request_at` (R7)

These are the **runtime** layer's concerns. The ModelRegistry is a catalog, not a runtime.

### 5. Runtime Manager + Runtime Registry (file-backed)

**Files:** `backend/app/services/runtime_manager.py`, `backend/app/services/runtime_registry.py`

The RuntimeManager carries the **operational state** of every runtime:
- `state` (`Installed` / `Starting` / `Active` / `Stopping` / `Stopped` / `Failed` / `Removed`)
- `host` / `port` (the runtime endpoint)
- `image_identity` (`{repository, tag, digest}`)
- `started_at` / `last_health_at` / `last_request_at` (R7)
- `health_state` (`Ready` / `NotReady` / `Unknown`)

The RuntimeRegistry holds the **declarative** descriptor:
- `image.repository` / `image.tag` / `image.digest`
- `build.{entrypoint, build_context, dockerfile}` (R2)
- `service.{port, paths}`
- `lifecycle.{install_policy, idle_timeout, ...}` (R7)
- `capabilities` (subset of the bound model)
- `requirements.{gpu, min_vram_gb, cpu_cores, memory_gb}`
- `model_binding.model_id` (the catalog id this runtime serves)

**There is no API endpoint that surfaces this state.** The runtime layer is built but not exposed.

### 6. The gap

The Models page:
- ✅ Reads from the catalog (DB) — real, accurate.
- ✅ Triggers install/activate via the API — real, but goes to the legacy path when no manager is attached.
- ❌ Does NOT see runtime state (image, port, host, readiness, uptime, last_request_at).
- ❌ Does NOT see the runtime-registry (the file-based catalog of runtimes).
- ❌ Does NOT show install/activate progress (the API returns 200 instantly, the UI flips state).
- ❌ Does NOT distinguish "image present, container not running" from "no image, no container".

## What is real, mocked, stale, or disconnected

| Concern | Status | Evidence |
|---|---|---|
| Catalog of 4 models (Kokoro, OmniVoice Base, OmniVoice Singing, Fish Audio S2 Pro) | **Real** | Seeded from `BUILTIN_MODELS` in `migrations.py`. |
| Catalog status (available, loaded, etc.) | **Mocked** | The DB status column is set by `model_lifecycle._set_status`, not by real runtime events. The "install" is a status flip; the "activate" is a status flip. |
| `Kokoro 82M` runtime descriptor | **Real** | `runtime-registry/kokoro-82m/descriptor.json`; loaded by `RuntimeRegistryLoader`. |
| Kokoro runtime install/activate | **Real (when wired)** | `model_lifecycle.install_model` delegates to `RuntimeManager.install` when the manager is attached. |
| Runtime state (Active/Installed/Stopped) | **Disconnected from UI** | The manager carries the state; no API endpoint surfaces it. |
| Install/activate progress | **Stale** | The API returns 200 instantly; the UI flips state without showing the actual lifecycle. |
| OmniVoice Singing, Fish Audio S2 Pro runtime descriptors | **Missing** | These models have no runtime-registry entry; they're catalog-only. |
| `OMNIVOICE_MODEL` setting | **Real** | `Settings.OMNIVOICE_MODEL = "k2-fsa/OmniVoice"`. Used by the in-process provider. |
| `KOKORO_RUNTIME_URL` setting | **Real** | Adapter data-plane; used by `KokoroAdapter` when set. |
| `RUNTIME_SERVICE_ENABLED` setting | **Real** | Infrastructure control plane; gates `wire_runtime_services` at startup. |

## What's needed (Tasks 3-7)

### Backend

1. **New endpoint:** `GET /api/runtimes` — list all runtimes in the registry, joined with cached state.
2. **New endpoint:** `GET /api/runtimes/{id}/state` — single runtime's operational state.
3. **New endpoint:** `GET /api/runtimes/{id}/state/stream` — Server-Sent Events for live state.
4. **New endpoint:** `GET /api/runtimes/{id}/logs` — async iterator over runtime logs.
5. **New endpoint:** `POST /api/runtimes/{id}/install` (and start/stop/update/remove) — direct runtime ops, not model-mapped.
6. **New endpoint:** `GET /api/runtimes/{id}/descriptor` — the on-disk descriptor.

### Frontend

1. **New hook:** `useRuntimes()` — calls `/api/runtimes`.
2. **New hook:** `useRuntime(id)` — calls `/api/runtimes/{id}/state`.
3. **New type:** `RuntimeCard` — represents a runtime in the UI.
4. **Models page refactor:** render from `useRuntimes()` when `RUNTIME_SERVICE_ENABLED=true`; otherwise render from `useModels()`.
5. **Runtime Operations Panel:** expanded card with image, port, host, uptime, health.
6. **Install/Activate progress UI:** subscribes to `/state/stream`; shows step-by-step state.
7. **Lifecycle states UI:** renders all 7 RuntimeState values (Not Installed, Pulling, Installed, Starting, Ready, Active, Stopping, Stopped, Failed, Updating).

## The cards the user is asking about

| Card | "Registered" | "Installed" | "Available" | "Active" |
|---|---|---|---|---|
| Today (DB) | Not in DB | `inactive` | `available` | `loaded` |
| Should be (Runtime) | Not in registry | `Installed` (image present, container not running) | `Active` (container running, `/ready` 200) | `Active` + readiness (== Available in this model) |
| Notes | — | "image pulled, install ok" | "container running, /ready 200" | legacy confusion; Active == Available in the runtime model |

**The right answer:** the runtime model collapses "Available" and "Active" into one (a runtime is either Active or not). The lifecycle states are: `Not Installed` → `Pulling` → `Installed` → `Starting` → `Active` → `Stopping` → `Stopped` → `Failed` → `Updating`.

## The fix, in one sentence

The Models page must render from `/api/runtimes` (a new endpoint backed by `RuntimeRegistry` + `RuntimeManager`) when `RUNTIME_SERVICE_ENABLED=true`. The legacy `/api/models` view is the fallback. The runtime layer is the source of truth for "is this runtime installed / running?"

---

**See also:**
[`docs/.agents/AUDITS/source-of-truth-audit.md`](source-of-truth-audit.md) (Task 1)
·
[`docs/.agents/SPECS/FEATURES/runtime-services-implementation/SPEC.md`](../SPECS/FEATURES/runtime-services-implementation/SPEC.md) (R3, R4, R6, R7)
·
[`frontend/src/app/models/page.tsx`](../../../frontend/src/app/models/page.tsx) (legacy view)
·
[`backend/app/api/models.py`](../../../backend/app/api/models.py) (catalog endpoint)
