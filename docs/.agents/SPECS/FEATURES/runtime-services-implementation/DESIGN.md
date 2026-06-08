# DESIGN — Runtime Services Implementation (Phase 2 ADR)

> **How it will be built.** SDD stage 3. References the
> [SPEC](./SPEC.md) and
> [ADR-0017](../../../DECISIONS/adr-0017-runtime-services-implementation.md).
> **Architecture only. No code, no `RuntimeManager` class, no
> `RuntimeDriver` class, no `RuntimeDescriptor` Pydantic class, no
> `runtime-registry/` directory, no Docker integration, no new API
> endpoints, no Kokoro migration code.**
>
> **Refinements (2026-06-08, post-audit):** see §1.1 (R2 — `spec.build`),
> §2.1 (R1 — self-contained entries), §3.7 (R3 — `RUNTIME_SERVICE_ENABLED`),
> §3.8 (R4 — runtime-first lifecycle), §9 (R4 — CE operations revised).

---

## Approach

ADR-0016 named the conceptual surface — Runtime Registry, Runtime
Manager, Runtime Driver, Runtime Service, RuntimeInstance. ADR-0017
*specifies* that surface: the descriptor schema, the registry model,
the manager's orchestration and resolution flows, the driver's
protocol and error contract, the wire contract of the Runtime Service,
the routing lifecycle, the Kokoro migration, and the CE/Cloud
operations.

The change is purely architectural in this phase. Phase 2
implementation can begin *after* ADR-0017 is accepted and TDD tasks
from [TASKS.md](./TASKS.md) are picked up.

Architectural flow is unchanged from ADR-0016:

```
Voice
  → VoiceVariant
    → Active Artifact (ADR-0009)
      → Adapter
        → Runtime Manager
          → Runtime Driver
            → Runtime Service
              → Inference
```

The Active Artifact resolution step is **mandatory** and **may not be
bypassed**.

---

## 1. RuntimeDescriptor

The `RuntimeDescriptor` is the canonical, declarative, machine-readable
description of a runtime. It is the **runtime contract** — the only
artifact required (in addition to the runtime image and the adapter)
to add a new model.

### 1.1 Schema

The descriptor is a JSON document, conventionally named
`descriptor.json`, co-located with the runtime source in the
registry:

```
runtime-registry/
└── <runtime_id>/
    ├── descriptor.json       ← this descriptor (the contract)
    ├── Dockerfile            ← CE build (R1, R2)
    ├── server.py             ← CE entrypoint (R1)
    ├── requirements.txt      ← CE runtime deps (R1)
    ├── README.md             ← operator documentation (R1)
    └── tests/                ← CE validation (R1)
```

Each entry is **self-contained**: the descriptor, the source to
build the image, the requirements, the operator documentation,
and the validation tests all live in one directory. The directory
is the runtime; the descriptor alone is not.

The full schema (field name → type → required → description):

| Field | Type | Required | Description |
|---|---|---|---|
| `api_version` | string | yes | Schema version. First version: `peakvox.io/v1`. |
| `kind` | string | yes | Always `Runtime`. |
| `metadata` | object | yes | Identity + human-readable metadata. |
| `spec` | object | yes | Behavior: image, build, capabilities, requirements, service contract. |

`metadata` sub-fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Unique runtime id (DNS-label, ≤ 63 chars). |
| `name` | string | yes | Human-readable runtime name. |
| `description` | string | no | One-paragraph description. |
| `provider` | string | yes | The model provider this runtime implements (e.g. `kokoro`, `f5-tts`). |
| `version` | string | yes | Runtime version string (semver recommended). |
| `edition` | list[string] | yes | Editions supported: subset of `["ce", "cloud"]`. |
| `labels` | map[string]string | no | Free-form labels for search/filter. |

`spec` sub-fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `runtime_type` | enum | yes | `docker` (first version). |
| `image` | object | yes | Image identity (always present, always used by `RuntimeManager`). |
| `build` | object | no | Local-build metadata (CE). Manager-agnostic; never read by `RuntimeManager`. |
| `service` | object | yes | The Runtime Service Contract. |
| `capabilities` | list[string] | yes | Subset of the model's `ModelCapabilities`. |
| `requirements` | object | yes | Host-side requirements. |
| `model_binding` | object | yes | Maps this runtime to a logical Model. |
| `lifecycle` | object | no | Install/update/health policy. |

`spec.image`:

| Field | Type | Required | Description |
|---|---|---|---|
| `repository` | string | yes | OCI image repository (e.g. `peakvox/kokoro-runtime`). |
| `tag` | string | yes | Image tag (e.g. `1.4.2` — never `latest` in production paths). |
| `digest` | string | no | Pin to a specific image digest (sha256:...). |

`spec.build` (R2 — local-build metadata, CE-only):

| Field | Type | Required | Description |
|---|---|---|---|
| `entrypoint` | string | yes | The file inside the image that is the HTTP service entrypoint (e.g. `server.py`). |
| `build_context` | string | yes | Path (relative to the descriptor's directory) used as the Docker build context. |
| `dockerfile` | string | no | Path to the Dockerfile (relative to `build_context`). Defaults to `Dockerfile`. |

The `build` block is **optional**. CE descriptors carry it so a
CE build script can `docker build` the image locally. Cloud
descriptors omit it; the `spec.image` is a published image in a
registry. **`RuntimeManager` never reads `spec.build`** — the
manager is image-agnostic. The build script is a pre-flight
concern of the registry loader / deployment tooling, never of
the manager or driver.

`spec.service`:

| Field | Type | Required | Description |
|---|---|---|---|
| `protocol` | enum | yes | `http` (first version) or `grpc` (future). |
| `port` | int | yes | Port the Runtime Service listens on inside the container. |
| `health_path` | string | no | Defaults to `/health`. |
| `readiness_path` | string | no | Defaults to `/ready`. |
| `generate_path` | string | no | Defaults to `/v1/generate`. |
| `build_path` | string | no | Defaults to `/v1/variants/build`. |
| `metadata_path` | string | no | Defaults to `/v1/metadata`. |

`spec.requirements`:

| Field | Type | Required | Description |
|---|---|---|---|
| `gpu` | enum | no | `required` / `optional` / `none`. Defaults to `optional`. |
| `min_vram_gb` | int | no | Required minimum VRAM. |
| `cpu_cores` | int | no | Required minimum CPU cores. |
| `memory_gb` | int | no | Required minimum memory. |
| `edition` | list[string] | no | Subset of `metadata.edition` — the editions for which this requirement applies. |

`spec.model_binding`:

| Field | Type | Required | Description |
|---|---|---|---|
| `model_id` | string | yes | The `Model.id` (catalog id) this runtime implements. |
| `is_default` | bool | no | If true, this runtime is the default for `model_id` in CE. |
| `priority` | int | no | Tiebreaker for runtime selection; lower is higher priority. |

`spec.lifecycle`:

| Field | Type | Required | Description |
|---|---|---|---|
| `install_policy` | enum | no | `pull-on-start` (default) / `pull-on-install` / `lazy`. |
| `health_interval_seconds` | int | no | Driver probes readiness at this interval. Defaults to 10. |
| `health_timeout_seconds` | int | no | Per-probe timeout. Defaults to 3. |
| `start_timeout_seconds` | int | no | Max wait for first `/ready` after start. Defaults to 60. |
| `restart_policy` | enum | no | `on-failure` (default) / `always` / `never`. |
| `idle_timeout` | enum | no | `never` (Cloud default) / `15m` (CE default) / `30m` / `1h` / `6h`. (R7) |

`idle_timeout` (R7) controls how long an Active runtime container
stays alive after the last `resolve()` call. The
`RuntimeManager` records `last_request_at` on every resolve and
runs a background reaper task that calls `stop_runtime` when
the configured timeout elapses. A subsequent `resolve()` triggers
re-activation. The default is `15m` in CE; `never` in Cloud
(autoscaler / scheduler owns lifecycle). Allowed values form a
closed vocabulary: `never`, `15m`, `30m`, `1h`, `6h`.

### 1.2 Example — full descriptor

```yaml
api_version: peakvox.io/v1
kind: Runtime

metadata:
  id: kokoro-cpu
  name: Kokoro CPU Runtime
  description: CPU-capable Kokoro 82M TTS runtime.
  provider: kokoro
  version: 1.4.2
  edition: [ce, cloud]
  labels:
    family: tts
    license: apache-2.0

spec:
  runtime_type: docker

  image:
    repository: peakvox/kokoro-runtime
    tag: "1.4.2"
    digest: sha256:abc123...     # pinned for reproducibility

  service:
    protocol: http
    port: 8000
    health_path: /health
    readiness_path: /ready
    generate_path: /v1/generate
    build_path: /v1/variants/build
    metadata_path: /v1/metadata

  capabilities:
    - tts
    - multilingual

  requirements:
    gpu: none                   # CPU-capable
    cpu_cores: 1
    memory_gb: 2
    edition: [ce, cloud]

  model_binding:
    model_id: kokoro-base
    is_default: true
    priority: 100

  lifecycle:
    install_policy: pull-on-install
    health_interval_seconds: 10
    health_timeout_seconds: 3
    start_timeout_seconds: 60
    restart_policy: on-failure
```

### 1.3 Identity rules

- `metadata.id` is the **runtime id**. It is unique within the
  registry. It is a DNS-label (lowercase, alphanumeric, `-`, `.`),
  ≤ 63 characters.
- `metadata.id` is **immutable** for the lifetime of a runtime. A new
  version = a new image (`spec.image.tag` / `digest`) bound to the same
  id. A renamed id is a new runtime.
- `metadata.id` must match the directory name under `runtime-registry/`
  (`runtime-registry/<metadata.id>/runtime.yaml`).

### 1.4 Versioning rules

- The descriptor itself has `api_version` (`peakvox.io/v1`).
  Future schema changes are additive within the same major; breaking
  changes get a new `api_version`.
- The image is versioned by `spec.image.tag` (semver) and pinned by
  `spec.image.digest` when present. The combination
  `(repository, tag, digest)` is the **immutable image identity**.
- `metadata.version` is the runtime version (semver). It moves in
  lockstep with image tag bumps; `1.4.2 → 1.4.3` is a runtime-level
  patch.

### 1.5 Runtime capabilities

- `spec.capabilities` is a **subset** of the model's
  `ModelCapabilities` (ADR-0003).
- The runtime cannot exceed the model. A runtime that declares
  `voice_cloning` while the model does not is **rejected at load
  time**.
- The empty set `[]` is valid for a runtime that, e.g., only
  rebuilds variants without serving inference (build-only runtimes —
  not in Phase 2, future).

### 1.6 Runtime requirements

- `spec.requirements.gpu = required` means the manager refuses to
  activate the runtime on a host without a GPU.
- `spec.requirements.gpu = optional` means the runtime can use a GPU
  if present, but does not require one.
- `spec.requirements.gpu = none` means the runtime must not see a GPU
  (e.g. CPU-only Kokoro).
- `min_vram_gb`, `cpu_cores`, `memory_gb` are minimums; the manager
  reports the host's capability and refuses activation on mismatch.

---

## 2. RuntimeRegistry

The Runtime Registry is a **file-based catalog** of `RuntimeDescriptor`
documents. It is not a database; it is a directory on disk.

### 2.1 Discovery model

```
<registry_root>/
├── kokoro-82m/
│   ├── descriptor.json     ← the contract
│   ├── Dockerfile          ← CE build (R1)
│   ├── server.py           ← CE entrypoint
│   ├── requirements.txt    ← CE runtime deps
│   ├── README.md           ← operator documentation
│   └── tests/              ← CE validation
├── f5-tts/
│   ├── descriptor.json
│   ├── Dockerfile
│   ├── server.py
│   ├── requirements.txt
│   ├── README.md
│   └── tests/
├── xtts/
├── openvoice/
├── fish-audio/
├── omnivoice-local/
├── omnivoice-cloud/
└── ...
```

`<registry_root>` is configured at startup (env var, default
`./runtime-registry/`). The registry is **read-only** at runtime —
descriptors are authored out-of-band, not mutated by the running
system.

Each entry is **self-contained** (R1): descriptor + source +
requirements + documentation + tests. A new runtime is added by
**copying a working entry and adjusting six fields in the
descriptor + the source in `server.py`**. The reference entry is
`kokoro-82m/`; the next runtime added (F5-TTS, XTTS, OpenVoice,
Fish, OmniVoice) follows the same shape.

### 2.2 Descriptor loading

The `RuntimeRegistryLoader` walks `<registry_root>`, reads each
`descriptor.json`, validates it against the descriptor schema, and
indexes the result.

Validation rejects:
- Missing required fields.
- Unknown fields (forward-compat is opt-in via `api_version`).
- Type mismatches.
- Capability that is not a subset of the bound model's declared
  capabilities.
- Edition mismatch (`spec.requirements.edition` not a subset of
  `metadata.edition`).
- (R1) A registry entry that has a `descriptor.json` but no
  `Dockerfile` (or vice-versa) is logged as a warning but not
  rejected — the registry may legitimately host prebuilt-only
  descriptors in Cloud. The CE build path rejects entries that
  lack the build files.

Failures are logged with the path of the offending file and the
runtime is excluded from the index; one bad descriptor does not
prevent the rest from loading.

### 2.3 Indexes

The loader builds three in-memory indexes (rebuilt on each load):

- **By id** — `id → descriptor`. Primary lookup.
- **By model_id** — `model_id → [id]`. Used by the Runtime Manager to
  answer "what runtimes implement model M?".
- **By capabilities** — `capability → [id]`. Future use (e.g.
  capability-driven auto-routing). Phase 2 reads from it but does not
  write to it.

### 2.4 Runtime lookup

The registry exposes:

- `get(id) → descriptor | None`
- `list() → [descriptor]`
- `list_for_model(model_id) → [descriptor]`
- `list_for_capability(capability) → [descriptor]`

The registry is **immutable from the perspective of the manager**; the
manager can re-load the registry (e.g. on SIGHUP) but cannot mutate
it. Future ADRs may add write paths; for Phase 2, descriptors are
files on disk.

### 2.5 Runtime lifecycle visibility

The registry holds **declarative** state (what *should* exist). The
Runtime Manager holds **operational** state (what *does* exist, what
is healthy, what endpoint is currently reachable).

The registry's lifecycle visibility is therefore:
- "I have a descriptor for this runtime." (yes/no)
- "This is the declared image identity." (repository + tag + digest)
- "This is the bound model and capabilities." (model_id, capabilities)

It does **not** hold running-state information. That belongs to the
Runtime Manager / RuntimeInstance.

### 2.6 Hot reload (deferred)

Hot reload on descriptor changes is **deferred** to a later phase.
Phase 2 loads the registry once at startup. Restarts pick up new
descriptors. A future ADR (OPEN_DECISIONS Decision 12+) can add hot
reload via file-watch or a control-plane signal.

---

## 3. RuntimeManager

The Runtime Manager is the **orchestration-only** component inside
the backend. ADR-0016 normalized this; ADR-0017 commits the
normalization as the contract.

### 3.1 Responsibilities (canonical, from ADR-0016)

The Runtime Manager **owns**:

- **Discovers** runtimes from the Runtime Registry; reads
  `runtime.yaml` descriptors.
- **Resolves endpoints** — knows which URL an adapter should call
  for a given runtime.
- **Delegates** all lifecycle operations to the Runtime Driver
  (install, update, remove, start, stop, restart, status, logs,
  health, metrics).
- **Reports status** — surfaces the driver's view of each
  `RuntimeInstance` to the rest of the system (API, adapters, ops).

The Runtime Manager **does NOT**:

- Execute model inference.
- Allocate GPUs (or any device).
- Load model weights.
- Import model frameworks (torch, transformers, kokoro, f5-tts,
  fish-audio, or any other model code).
- Perform substrate-specific operations (Docker / Kubernetes /
  Podman / shell calls). Substrate-specific code lives only inside
  concrete driver implementations.
- Mutate the Runtime Registry (read-only at runtime).

### 3.2 Boundaries

The Runtime Manager's only collaborators are:

- **The Runtime Registry** — read-only access.
- **The Runtime Driver** — call-through to the substrate.
- **The Adapter** — receives the resolved endpoint from the manager.
- **The API layer** — receives install/activate/update/remove/status
  requests and surfaces status reports.

The Runtime Manager is **not** instantiated per request. There is
exactly one Runtime Manager per backend process, shared across the
FastAPI app. It owns the registry loader and the active driver.

### 3.3 Orchestration flow

The manager's request handling is a thin, well-defined pipeline. The
canonical flow for an API-driven install request is:

```
API
  → RuntimeManager.install(runtime_id)
    → registry.get(runtime_id) → descriptor
      → if descriptor is None: raise RuntimeNotFound
      → driver.install_runtime(runtime_id, descriptor)
        → driver returns RuntimeInstance { state: "Installed" }
      → manager stores (runtime_id → RuntimeInstance) in cache
        → return RuntimeInstance to API
```

The same pattern applies to update, remove, activate, deactivate,
restart, status, logs, health, metrics. The manager is a **cache +
delegate**; the driver does the work.

### 3.4 Runtime resolution flow

Adapters ask the manager for an endpoint. The canonical flow:

```
Adapter
  → RuntimeManager.resolve(model_id, hint=None)
    → registry.list_for_model(model_id) → [descriptor]
      → if empty: raise NoRuntimeForModel(model_id)
      → select descriptor
        → prefer descriptor where is_default = true
        → tiebreak by priority asc
        → if hint is given (e.g. "cuda"), filter by hint
      → look up the active RuntimeInstance for the chosen id
        → if missing or not Active:
          → driver.start_runtime(runtime_id) → instance
          → cache the instance
        → touch last_request_at = now (R7)
        → return endpoint
          → build endpoint as
              f"{protocol}://{instance.host}:{instance.port}"
            where protocol/port come from descriptor and
            host comes from the RuntimeInstance
```

Selection rules (deterministic, auditable):
1. **Edition filter** — the runtime must declare the current
   edition in `metadata.edition`.
2. **Default** — `model_binding.is_default = true` wins.
3. **Priority** — `model_binding.priority` ascending.
4. **Hint** — if the caller passes a hint (e.g. "cuda", "cpu",
   "local", "cloud"), filter descriptors whose `labels` or id match
   the hint.
5. **First match** — if still ambiguous, the first descriptor in
   registry order.

**Activation is lazy (R6).** The backend boots with **zero** active
runtimes; the first `resolve(model_id)` call triggers
`start_runtime` if the instance is not already `Active`. The
manager maintains an in-memory map
`(runtime_id → RuntimeInstance)` that the driver populates and
updates. The cache is empty at backend startup; the manager does
not pre-warm any runtime.

**Idle reaping (R7).** The manager records `last_request_at` on
every successful `resolve()`. A background task wakes up
periodically and calls `stop_runtime` for any Active instance
whose `last_request_at` is older than `descriptor.lifecycle.idle_timeout`.
The instance stays in the cache in `Installed` state (image
preserved) so the next `resolve()` can re-activate it without a
re-pull. `idle_timeout = never` (Cloud default) disables the
reaper.

### 3.5 Concurrency and consistency

- A single in-process lock guards the
  `(runtime_id → RuntimeInstance)` cache. Concurrent first requests
  for the same runtime serialize on the lock; the second request
  waits and reuses the first's instance.
- The manager does **not** persist operational state. After a
  backend restart, the cache is empty and runtimes must be
  re-activated. This is **explicitly** the Phase 2 design; a future
  ADR adds persistence (OPEN_DECISIONS Decision 12+).
- The manager does **not** pre-warm any runtime at startup (R6).
  The cache is empty by construction until the first `resolve()`.

### 3.6 Observability

The manager emits structured events for every state transition:

- `runtime.discovered` (registry load complete; counts)
- `runtime.install.requested` / `runtime.install.completed` /
  `runtime.install.failed`
- `runtime.start.requested` / `runtime.start.completed` /
  `runtime.start.failed`
- `runtime.stop.requested` / `runtime.stop.completed`
- `runtime.update.requested` / `runtime.update.completed`
- `runtime.remove.requested` / `runtime.remove.completed`
- `runtime.health.changed` (ready/unready transitions)
- `runtime.idle.timeout` (auto-stopped by the reaper, R7)
- `runtime.idle.touch` (every `resolve()` updates `last_request_at`)

These events are emitted via the existing `app.core.events` channel
(or whatever the project's structured event bus is at implementation
time). They are **not** domain events (no `generation.*`; no
`variant.*`).

### 3.7 Settings — `RUNTIME_SERVICE_ENABLED` (R3)

The runtime subsystem is opt-in at backend startup. The
`Settings` class gains a new field:

```python
RUNTIME_SERVICE_ENABLED: bool = False  # CE default; Cloud default true (future)
```

| Edition | Default | Rationale |
|---|---|---|
| Community Edition | `False` | The default CE experience continues to work in-process. Opt-in to Runtime Services. |
| Cloud | `True` (future) | Cloud is built around the runtime subsystem. |

When the flag is `False`:

- `main.py` lifespan does **not** call
  `attach_runtime_manager(...)`.
- The runtime subsystem is dead code in the running process.
- The Models page uses the legacy DB-status mock
  (`model_lifecycle.install_model` / `activate_model` are pure
  status transitions; no runtime ops are attempted).
- The in-process adapter path is the only path.

When the flag is `True`:

- `main.py` lifespan constructs `RuntimeRegistryLoader`,
  `DockerRuntimeDriver`, and `RuntimeManager`, then calls
  `PeakVoxRuntime.attach_runtime_manager(manager)`.
- The Models page routes Install/Activate/Deactivate/Update/Remove
  through the manager.
- The adapter path dispatches on `KOKORO_RUNTIME_URL` (adapter
  data-plane config) per the 2C contract; the manager activation
  is **independent** of the adapter's URL setting.

**The flag governs infrastructure wiring, not adapter routing.**
`KOKORO_RUNTIME_URL` remains the adapter's data-plane setting.

### 3.8 Lifecycle direction — Runtime first, Model status derived (R4)

The Model is a **catalog entity**. The Runtime is the
**operational entity**. Model status must reflect runtime state;
runtime state must not reflect model state.

The canonical lifecycle:

```
[Operator clicks "Install" on a Model in the Models page]
  → backend resolves model_id → default runtime_id via registry
    → RuntimeManager.install(runtime_id)
      → driver.install_runtime (docker pull, instance in Installed state)
        → cache the instance
  → on install success: model.status ← INSTALLED

[Operator clicks "Activate"]
  → RuntimeManager.activate(runtime_id)
    → driver.start_runtime (container started, /ready probed)
      → instance in Active state, health_state Ready
  → on activate success: model.status ← ACTIVE

[Runtime becomes idle for idle_timeout (R7)]
  → reaper: driver.stop_runtime (container stopped, image preserved)
    → instance in Installed state (not removed)
  → model.status ← INSTALLED (runtime is still installed, just inactive)

[Operator clicks "Remove"]
  → RuntimeManager.remove(runtime_id)
    → driver.remove_runtime (container stopped, image removed)
  → on remove success: model.status ← NOT_INSTALLED
```

Model status values derived from runtime state:

| Model status | Meaning | Runtime state |
|---|---|---|
| `NOT_INSTALLED` | No runtime is installed for this model. | No cached instance, or instance `Removed`. |
| `INSTALLED` | Runtime image is present, container is not running. | Cached instance in `Installed` or `Stopped` state. |
| `ACTIVE` | Runtime is serving inference. | Cached instance in `Active` state with `health_state = Ready`. |
| `FAILED` | Last install/start attempt failed. | Cached instance in `Failed` state. |

The Models page **never** directly sets `model.status`; the
manager's transition events update the status row. The transition
is a side-effect of the runtime transition, never the cause.

---

## 4. RuntimeDriver

The `RuntimeDriver` is the **substrate abstraction**. It is a
formal `Protocol` that the Runtime Manager depends on and that
concrete drivers (Docker, Kubernetes, Podman, local-process)
implement.

### 4.1 Protocol

`RuntimeDriver` is a Python `typing.Protocol` (structural). The
concrete class does not need to inherit; it only needs to expose
the methods below with the right signatures.

### 4.2 Operations (frozen from ADR-0016)

The 10 normative operations:

| # | Method | Returns | Purpose |
|---|---|---|---|
| 1 | `install_runtime(runtime_id, descriptor) → RuntimeInstance` | Pull image; register instance. |
| 2 | `update_runtime(runtime_id, descriptor) → RuntimeInstance` | Re-pull, possibly restart. |
| 3 | `remove_runtime(runtime_id) → None` | Stop, delete image, unregister. |
| 4 | `start_runtime(runtime_id) → RuntimeInstance` | Bring up the instance. |
| 5 | `stop_runtime(runtime_id) → None` | Tear down the instance. |
| 6 | `restart_runtime(runtime_id) → RuntimeInstance` | Stop + start. |
| 7 | `runtime_status(runtime_id) → RuntimeInstance` | Current state + endpoint. |
| 8 | `runtime_logs(runtime_id, since=None) → LogStream` | Stream of logs. |
| 9 | `runtime_health(runtime_id) → HealthReport` | Liveness + readiness. |
| 10 | `runtime_metrics(runtime_id) → Metrics` | Optional / future-safe. |

`RuntimeInstance`:

| Field | Type | Description |
|---|---|---|
| `runtime_id` | string | The runtime id. |
| `state` | enum | `Installed`, `Starting`, `Active`, `Stopping`, `Stopped`, `Failed`, `Removed`. |
| `host` | string | Reachable host (loopback, container IP, service DNS, pod IP, etc.). |
| `port` | int | The port from `descriptor.spec.service.port`. |
| `image_identity` | object | `{repository, tag, digest}` (immutable once installed). |
| `started_at` | datetime | When the instance last entered `Active`. |
| `last_health_at` | datetime | When health was last probed. |
| `health_state` | enum | `Ready`, `NotReady`, `Unknown`. |

`HealthReport`:

| Field | Type | Description |
|---|---|---|
| `runtime_id` | string | The runtime id. |
| `liveness` | enum | `Alive`, `Dead`. |
| `readiness` | enum | `Ready`, `NotReady`, `Unknown`. |
| `last_error` | string \| None | Last error from the substrate, if any. |
| `checked_at` | datetime | When the probe ran. |

`LogStream`: an async iterator over log lines (driver-specific;
the manager exposes a `GET /api/v1/runtimes/{id}/logs` endpoint that
streams from this).

### 4.3 Lifecycle semantics

**Install.** Pull the image. Allocate any host resources. Create the
instance record with state `Installed`. The instance is **not yet
serving**; the manager may call `start_runtime` to bring it up, or
the next resolve call triggers lazy start (see §3.4).

**Update.** Stop the instance if `Active`. Pull the new image. The
new image's `(repository, tag, digest)` becomes the new
`image_identity`. The instance is left in state `Installed`; lazy
start brings it up.

**Remove.** Stop the instance if `Active`. Remove the image.
Unregister the instance. The descriptor remains in the registry
until the registry itself is edited.

**Start.** Allocate runtime resources (e.g. start the container).
Probe `/ready` until it returns 200 or the
`lifecycle.start_timeout_seconds` elapses. On success, state becomes
`Active`, `health_state` becomes `Ready`. On timeout, state becomes
`Failed`, error captured.

**Stop.** Graceful shutdown (signal, then kill after a per-driver
timeout). State becomes `Stopped`. Image is preserved (so the next
`start` is fast).

**Restart.** Stop + start.

**Status.** Snapshot the current `RuntimeInstance`. No side effects.

**Logs.** Stream from the substrate's log source (Docker logs, K8s
pod logs, etc.). The driver does not interpret log lines.

**Health.** Run `/health` and `/ready` probes; return a
`HealthReport`. No side effects beyond the probes themselves.

**Metrics.** Driver-specific; Phase 2 may return an empty
`Metrics` object and rely on external monitoring for the first
version.

### 4.4 Error handling

#### 4.4.1 Error categories

The driver raises `RuntimeDriverError` subclasses. The manager
catches them, logs them, and translates them into API responses
(see §4.4.2).

| Exception | Cause | Manager action |
|---|---|---|
| `RuntimeNotFound` | `runtime_id` is not registered. | 404. |
| `ImagePullError` | Image pull failed (network, auth, missing). | 502 with reason. |
| `SubstrateError` | Generic substrate failure (Docker daemon down, etc.). | 502 with reason. |
| `RuntimeAlreadyExists` | Install when an instance is already present. | 409. |
| `RuntimeNotActive` | Operation requires an `Active` instance (e.g. logs). | 409. |
| `TimeoutError` | Operation exceeded its timeout. | 504. |
| `RuntimeRequirementsNotMet` | Host does not satisfy `spec.requirements`. | 422. |
| `RuntimeHealthFailed` | Readiness probe failed during start. | 503 with reason. |

#### 4.4.2 Propagation

The manager does **not** swallow errors. It:
1. Logs the error with the runtime id and the operation.
2. Emits a `runtime.<op>.failed` event.
3. Re-raises the exception (or returns a 4xx/5xx response in the API
   handler).

#### 4.4.3 Retries

- **Idempotent operations** (`install_runtime` when the same
  `(repository, tag, digest)` is already present) are no-ops and
  return the existing instance.
- **Network-failable operations** (`install_runtime` image pull,
  `start_runtime` first probe) may retry up to 3 times with
  exponential backoff (1s, 2s, 4s).
- **State-changing operations** (`stop_runtime`, `remove_runtime`)
  do **not** retry on failure — the operator must inspect.

#### 4.4.4 Timeouts

Default per-operation timeouts (the driver may override per
descriptor via `spec.lifecycle.*`):

| Operation | Default timeout |
|---|---|
| `install_runtime` (image pull) | 300s |
| `start_runtime` (until `/ready` returns 200) | 60s (`spec.lifecycle.start_timeout_seconds`) |
| `stop_runtime` | 30s |
| `health` (`/health` + `/ready` probe) | 3s per probe (`spec.lifecycle.health_timeout_seconds`) |
| `update_runtime` (stop + pull + start) | 300s + 60s = 360s |
| `remove_runtime` | 30s |

---

## 5. DockerRuntimeDriver

The first concrete driver. It implements `RuntimeDriver` against the
Docker Engine API (via the official Docker SDK for Python, or a thin
CLI fallback if the SDK is unavailable in the runtime image).

### 5.1 Responsibilities

The `DockerRuntimeDriver`:

- Pulls the image declared in `descriptor.spec.image`.
- Creates a container with the runtime image, mapping
  `descriptor.spec.service.port` to a host port (or bridge IP).
- Configures environment variables from `descriptor.spec` (e.g.
  `MODEL_ID`, runtime-specific tunables).
- Mounts the artifact store as a volume (read-only) so the runtime
  can read Voice Source Assets and VoiceVariantArtifacts.
- Probes `/health` and `/ready` from
  `descriptor.spec.service.{health_path, readiness_path}`.
- Streams container logs through `runtime_logs`.
- Implements the full 10-operation `RuntimeDriver` protocol.

### 5.2 Boundaries

The `DockerRuntimeDriver` does **NOT**:

- Talk to Kubernetes. (Separate driver; separate ADR.)
- Talk to Podman. (Separate driver.)
- Run on a remote Docker host. (Phase 2 is local Docker only; remote
  hosts are a future ADR.)
- Manage Docker networks. The runtime container is created on a
  default bridge network; custom networks are a future ADR.
- Manage Docker volumes beyond the artifact store mount. State
  inside the runtime container is ephemeral.
- Run privileged. The runtime image is responsible for whatever
  device access it needs (e.g. NVIDIA Container Toolkit for GPU).

### 5.3 Image identity and pinning

- The driver reads `(repository, tag, digest)` from the descriptor.
- If `digest` is present, the driver pulls *by digest* (`@sha256:...`).
  Tag-only pulls are not used in production paths.
- The image identity is stored on the `RuntimeInstance` and
  surfaced through `runtime_status`.

### 5.4 Container lifecycle

- Container name: `peakvox-runtime-<runtime_id>`.
- Restart policy: `descriptor.spec.lifecycle.restart_policy` →
  Docker `--restart` flag (`on-failure` → `on-failure`,
  `always` → `always`, `never` → `no`).
- Labels: `peakvox.runtime.id`, `peakvox.runtime.model_id`,
  `peakvox.edition` (for `docker ps` filtering).

### 5.5 Substrate error mapping

Docker SDK errors map to `RuntimeDriverError` subclasses:

- `ImageNotFound` → `ImagePullError` (404 from registry).
- `APIError(500)` from Docker daemon → `SubstrateError`.
- `NotFound` on container lookup → `RuntimeNotFound`.
- Timeout on `/ready` → `RuntimeHealthFailed`.
- Host doesn't have GPU when `requirements.gpu = required` →
  `RuntimeRequirementsNotMet`.

---

## 6. Runtime Service Contract

Every Runtime Service MUST expose the same five HTTP/JSON endpoints.
The contract is **model-neutral** — Kokoro, F5-TTS, Fish, OmniVoice,
and any future provider all implement the same five endpoints,
shaped the same way.

The contract is documented here as the canonical wire format. Phase 2
implementation will codify it as OpenAPI 3.1 and version it
(`peakvox.io/v1`).

### 6.1 `GET /health` — Liveness

- **Purpose:** Is the process alive and responding?
- **Request:** no body.
- **Response 200:** `{"status": "alive"}`
- **Response 503:** `{"status": "dead", "reason": "<short reason>"}`
- **Manager semantics:** A 503 means the driver should restart the
  instance. A 200 means the process is up; it does **not** mean the
  runtime is ready to serve inference.

### 6.2 `GET /ready` — Readiness

- **Purpose:** Can the runtime actually serve inference right now?
- **Request:** no body.
- **Response 200:** `{"status": "ready"}`
- **Response 503:** `{"status": "not_ready", "reason": "weights_loading"}` (or another short reason)
- **Manager semantics:** A 200 here is the **only** signal that the
  manager may route traffic to the instance. A 503 means the manager
  refuses to resolve this instance; the adapter's call falls back to
  the in-process path (Phase 2) or to a different runtime (future).

The readiness response distinguishes between
`not_ready` reasons because the manager may use them for routing
decisions in the future (e.g. "weights_loading" → wait;
"unsupported_request" → fail-fast; "maintenance" → drain).

### 6.3 `POST /v1/generate` — Generation

- **Request:**

  ```json
  {
    "voice_id": "voice_abc123",
    "variant_id": "variant_xyz789",
    "artifact_id": "artifact_def456",
    "artifact_version": 3,
    "text": "Hello, world.",
    "language": "en",
    "params": { "speed": 1.0, "num_step": 32 },
    "request_id": "req_...",
    "callback_url": "https://..." 
  }
  ```

- **Field semantics:**
  - `voice_id` is the public voice id (ADR-0001).
  - `variant_id` is the `VoiceVariant` row id.
  - `artifact_id` + `artifact_version` is the **active artifact**
    (ADR-0009). The runtime pins to this version for reproducibility.
  - `text`, `language`, `params` are the model-specific generation
    inputs.
  - `request_id` is a client-supplied UUID for log correlation.
  - `callback_url` is optional; if present, the runtime POSTs the
    result to the URL when generation completes (for long-running
    requests). If absent, the runtime streams the audio back in the
    response.

- **Response 200 (streaming):** audio bytes (`audio/wav` or
  `audio/ogg` — content-negotiated via `Accept` header).
  Headers: `X-Peakvox-Duration-Ms`, `X-Peakvox-Request-Id`,
  `X-Peakvox-Logs` (optional base64-encoded log tail).

- **Response 200 (callback):** `{"request_id": "req_...",
  "status": "accepted"}`. The result arrives at `callback_url` as a
  separate POST.

- **Response 4xx/5xx:** JSON error body
  `{"error": {"category": "...", "message": "...", "request_id": "..."}}`.

### 6.4 `POST /v1/variants/build` — Variant build

- **Request:**

  ```json
  {
    "voice_id": "voice_abc123",
    "reference_audio_storage_key": "voice_assets/voice_abc123/source.wav",
    "params": { "...": "..." }
  }
  ```

- **Field semantics:**
  - `voice_id` is the public voice id.
  - `reference_audio_storage_key` points to the canonical Source Asset
    in the artifact store (ADR-0010). The runtime reads it, builds
    the variant, and returns the new artifact identity.

- **Response 200:**

  ```json
  {
    "variant_id": "variant_xyz789",
    "artifact_id": "artifact_def456",
    "artifact_version": 3,
    "status": "ready"
  }
  ```

- **Response 202 (async build):** same shape, `"status": "building"`.
  The runtime accepts the build; the manager polls
  `GET /v1/variants/{variant_id}` (or, in Phase 2, queries the
  adapter's existing `build_variant` path) until `status = ready`.

- **Response 4xx/5xx:** standard error body.

### 6.5 `GET /v1/metadata` — Metadata

- **Request:** no body.
- **Response 200:**

  ```json
  {
    "runtime_id": "kokoro-cpu",
    "model_id": "kokoro-base",
    "capabilities": ["tts", "multilingual"],
    "supported_languages": ["en", "es", "fr", "..."],
    "supported_tags": ["happy", "sad", "..."],
    "realization_types": ["voice_pack"],
    "build_strategies": [
      {
        "creation_source": "PRESET_VOICE",
        "can_build": true,
        "requires": ["preset_name"]
      }
    ],
    "max_concurrent_requests": 4,
    "max_text_length": 5000
  }
  ```

- **Manager semantics:** The manager calls this once per
  `start_runtime` and caches the result. The adapter uses the
  cached metadata for capability / language / tag validation in
  step 4 of the routing flow (§7).

### 6.6 Error body (canonical)

All error responses use the same shape:

```json
{
  "error": {
    "category": "validation | capability_mismatch | not_ready | substrate | timeout | internal",
    "message": "human-readable message",
    "request_id": "req_...",
    "timestamp": "2026-06-07T12:34:56.789Z"
  }
}
```

This matches the existing `ApiError` shape in the backend (see
`backend/app/main.py` exception handlers added in
`4d5db88 feat(errors)`).

---

## 7. Runtime Routing

The complete request lifecycle, with error handling at every step.
This is the canonical flow for every model that has a runtime
service. Models without a runtime service fall back to the in-process
path (Phase 2+ until Phase 7).

### 7.1 Happy path

```
1. authenticate
   principal = current user
   on failure: 401

2. resolve voice
   voice = Voice(public_voice_id)
   on failure: 404 voice_not_found

3. route model
   model = Model(model_id)  [explicit | default | auto]
   on failure: 404 model_not_found

4. validate capabilities
   if request.capabilities ⊄ model.capabilities: 422 capability_mismatch

5. ensure variant
   variant = ensure_variant(voice, model)  [ADR-0008]
   on failure: 409 variant_failed | 202 variant_building

6. resolve active artifact
   artifact = active_artifact(variant)  [ADR-0009]
   on failure: 404 artifact_not_found

7. acquire adapter
   adapter = ModelAdapter(model_id)

8. acquire runtime endpoint
   endpoint = RuntimeManager.resolve(model_id)  [§3.4]
   on failure:
     - RuntimeNotInstalled → 503 runtime_not_installed
     - RuntimeRequirementsNotMet → 422 runtime_requirements
     - NoRuntimeForModel → 503 no_runtime_for_model
     - In CE without Docker: 503 docker_unavailable (fallback to step 8b)

8b. (CE-only, in-process fallback)
   if KOKORO_RUNTIME_URL is unset or empty:
     proceed in-process via the existing adapter.generate path
     skip steps 9-12

9. fetch metadata (cached)
   metadata = cached metadata for runtime_id (from prior start)
   on cache miss: GET /v1/metadata → cache

10. translate + send
    request_payload = adapter.translate_generate(
        variant=variant, artifact=artifact, text=text, params=params
    )
    response = POST {endpoint}/v1/generate
    on failure:
      - 5xx substrate → 502 runtime_substrate_error
      - 4xx capability / validation → 422 / 400 forwarded
      - timeout → 504

11. deliver
    audio = response.body (or fetched from callback URL)
    store under storage_key
    return URL to caller

12. emit
    event("generation.completed", voice_id, model_id, duration_ms)
```

### 7.2 Failure handling matrix

| Step | Failure | Status | Notes |
|---|---|---|---|
| 1 | Auth fails | 401 | Existing `AuthProvider` seam. |
| 2 | Voice not found | 404 | Existing. |
| 3 | Model not found | 404 | Existing. |
| 4 | Capability mismatch | 422 | Existing. |
| 5 | Variant missing | 202 + job_id | Existing async behavior. |
| 5 | Variant failed | 409 | Existing. |
| 6 | Artifact missing | 500 | Should never happen; invariant of `ensure_variant`. |
| 7 | Adapter missing | 500 | Should never happen; invariant of `ModelAdapter` registry. |
| 8 | Runtime not installed | 503 | Trigger install + retry once. |
| 8 | Runtime requirements not met | 422 | Operator action required. |
| 8 | No runtime for model | 503 | No runtime descriptor matches. |
| 8 | Docker unavailable (CE) | 503 | Fall through to 8b. |
| 8b | In-process fallback fails | 5xx | Existing in-process errors. |
| 9 | Metadata fetch fails | 503 | Manager caches empty; adapter still attempts generation. |
| 10 | Substrate 5xx | 502 | Driver surface; manager re-raises. |
| 10 | Substrate 4xx | 4xx | Forwarded. |
| 10 | Timeout | 504 | Adapter's existing timeout policy. |
| 11 | Storage write fails | 500 | Existing. |
| 12 | Event emission fails | log + continue | Existing. |

### 7.3 Routing invariants

- **Steps 1-7 are unchanged** from the pre-Phase-2 generation
  flow. The Runtime Service slot is between adapter selection and
  generation.
- **Step 8 is new.** The first time the runtime service path is
  exercised, the manager may need to start the instance
  (lazy activation). After the first call, the instance is cached.
- **Step 8b is the additive fallback.** In CE, if Docker is not
  available, the adapter falls back to in-process. In Cloud,
  step 8b does not exist (the cloud runtime is always available or
  the request fails).
- **The adapter remains responsible** for translating PeakVox
  concepts to the runtime protocol (step 10's
  `adapter.translate_generate`).

---

## 8. Kokoro Migration

Kokoro is the **first model** to be migrated to a remote runtime
service in Phase 3. ADR-0017 makes the migration architecture
explicit; Phase 3 will execute it.

### 8.1 Current state

- `KokoroAdapter` is in-process (`backend/app/services/model_adapters/kokoro_adapter.py`).
- It imports the `kokoro` pip package lazily inside methods.
- It exposes the full `ModelAdapter` surface
  (`generate`, `build_variant`, `health_check`, capabilities,
  supported languages / tags, realization types, build strategies).
- It is the only non-OmniVoice model with provider validation
  (G5 passed).
- It is CPU-capable (82M params); no GPU required.

### 8.2 Target state

- A `peakvox/kokoro-runtime` Docker image exists, exposing the
  Runtime Service Contract over HTTP.
- `KokoroAdapter` becomes a **protocol translator**: it talks to
  the runtime service when one is reachable; otherwise it falls
  back to in-process execution.
- The adapter is configured with `KOKORO_RUNTIME_URL` (default:
  unset). When unset, the in-process path is used (no behavior
  change for existing users). When set, all generation routes
  through the runtime.
- The runtime image is versioned (`peakvox/kokoro-runtime:1.4.2`
  for the first version). The runtime image version moves in
  lockstep with the `kokoro` pip package version.
- The migration is **additive** until Phase 7 explicitly removes
  the in-process path.

### 8.3 Migration strategy

The migration is a four-step rollout. Each step is independently
reversible.

#### Step 1 — Runtime image published (no behavior change)

- Build and publish `peakvox/kokoro-runtime:0.1.0` (HTTP server
  wrapping the `kokoro` pip package).
- `KokoroAdapter` is **unchanged**. The runtime image is not yet
  wired.
- Validation: `GET /health` and `GET /ready` return 200 inside
  the container; `POST /v1/generate` produces real audio for a
  fixture input.

#### Step 2 — Adapter transport added (still no behavior change)

- `KokoroAdapter` gains an `HTTPTransport` (gated by
  `KOKORO_RUNTIME_URL`).
- When the env var is unset, the adapter behaves identically
  to today (in-process). When the env var is set, the adapter
  routes to the runtime — but this is opt-in only.
- Validation: regression tests pass in both modes.

#### Step 3 — Runtime enabled in CE (additive)

- Set `KOKORO_RUNTIME_URL=http://peakvox-kokoro:8000` in the
  default `docker-compose.yml` for CE installations that include
  the Kokoro runtime.
- The in-process path remains as a fallback for users who run
  PeakVox without Docker.
- Validation: end-to-end generation works through the runtime
  service; in-process fallback also works.

#### Step 4 — In-process path deprecated (Phase 7)

- A future ADR (Phase 7's "Remove direct in-process model
  execution" ADR) marks the in-process path as deprecated
  and removes it.
- Until that ADR is accepted, both paths coexist.

### 8.4 Rollback strategy

Rollback is **at-most one environment variable**:

- **Roll forward (in-process fallback):** unset
  `KOKORO_RUNTIME_URL`. The adapter reverts to in-process
  execution. No data migration. No schema change. The runtime
  container can be stopped; it is no longer routed to.
- **Roll back (image issue):** if the runtime image has a bug,
  the previous image tag is still pinned in the descriptor.
  Edit the descriptor to point to the previous tag
  (`peakvox/kokoro-runtime:1.4.1` instead of `1.4.2`); restart
  the runtime via `RuntimeManager.update_runtime`. The old
  image is pulled and the new instance is created.

The rollback is **declarative**: the descriptor is the source of
truth, and rollback is a descriptor change. There is no in-place
mutable state to roll back.

### 8.5 Data and schema impact

- **No DB schema changes** for Phase 2's Kokoro migration. The
  `models` table row for `kokoro-base` already exists.
- **A possible `runtime_binding` column** on `models` is deferred
  to Phase 3+ when the migration is provider-validated. ADR-0017
  does not introduce it.
- **The artifact store** is unchanged. The runtime reads
  Source Assets and VoiceVariantArtifacts from the existing
  storage abstraction (`app.services.storage`).

---

## 9. Community Edition operations

CE is the first edition in which the Runtime Service architecture
becomes operational. The operations are uniform at the Runtime
Manager level; the `DockerRuntimeDriver` provides the CE-specific
substrate. Per R4, the lifecycle is **Runtime first, Model status
derived**.

### 9.1 Install — pull image, create Installed instance

Operator flow (typically triggered from the Models page):

1. Operator clicks "Install" on a model in the Models page.
2. The backend resolves `model_id` → the default `runtime_id` via
   the registry (`is_default = true`, highest `priority`).
3. The API calls `RuntimeManager.install(runtime_id)`.
4. The manager:
   - Reads the descriptor from the registry.
   - Calls `DockerRuntimeDriver.install_runtime(runtime_id, descriptor)`.
   - The driver pulls the image.
   - The instance is created in state `Installed`.
   - The manager caches the instance.
5. On install success: `model.status ← INSTALLED` (the model
   row's status is updated as a side-effect of the runtime
   transition).

Result: image present locally, container NOT running. The runtime
is ready to be activated.

### 9.2 Activate — start container, runtime becomes Ready

Operator flow:

1. Operator clicks "Activate" on a model.
2. The API calls `RuntimeManager.activate(runtime_id)`.
3. The manager:
   - Calls `DockerRuntimeDriver.start_runtime(runtime_id)`.
   - The driver starts the container.
   - The driver probes `/ready` until 200 or
     `lifecycle.start_timeout_seconds` elapses.
   - On success: state `Active`, `health_state` `Ready`.
   - The manager records `last_request_at = now` (R7).
4. On activate success: `model.status ← ACTIVE`.

The first **resolve** call (§3.4) triggers activation lazily if
the instance is `Installed` and the model is not yet `Active`.
Manual activation is for warm-up scenarios.

### 9.3 Deactivate — stop container, runtime remains installed

Operator flow:

1. Operator clicks "Deactivate" on a model.
2. The API calls `RuntimeManager.deactivate(runtime_id)`.
3. The manager:
   - Calls `DockerRuntimeDriver.stop_runtime(runtime_id)`.
   - The container is stopped; the image is preserved.
   - State becomes `Installed` (or `Stopped`).
4. On deactivate success: `model.status ← INSTALLED` (the image
   is still present, container is not running).

Result: container stopped, image preserved. The next Activate
call is fast (no re-pull).

### 9.4 Idle reaping — auto-stop after `idle_timeout`

The manager runs a background reaper task. Periodically (e.g. every
60 seconds), the reaper:

1. Iterates the instance cache.
2. For each `Active` instance, checks
   `now - last_request_at > descriptor.lifecycle.idle_timeout`.
3. If true, calls `driver.stop_runtime(runtime_id)`.
4. Emits `runtime.idle.timeout` event.
5. The manager's cache entry transitions to `Installed`; the
   image is preserved.

A subsequent `resolve()` call triggers re-activation (warm
start — the image is local; no re-pull). `idle_timeout = never`
disables the reaper for that runtime (Cloud default).

### 9.5 Update — re-pull, leave Installed

Operator flow:

1. Author a new descriptor (or update the image tag / digest
   directly in the existing descriptor).
2. Trigger `RuntimeManager.update(runtime_id)`.
3. The manager:
   - If the instance is `Active`, calls `stop_runtime` first.
   - Calls `update_runtime` (the driver re-pulls the new image).
   - Leaves the instance in state `Installed` (lazy start brings
     it up on next resolve).
4. The Active Artifact (ADR-0009) is **preserved** across updates.
   The runtime re-reads the artifact on next generation.

### 9.6 Remove — stop + remove image

Operator flow:

1. Operator clicks "Remove" on a model.
2. The API calls `RuntimeManager.remove(runtime_id)`.
3. The manager:
   - Calls `remove_runtime` (the driver stops the container if
     active, removes the image).
   - Drops the instance from the cache.
4. On remove success: `model.status ← NOT_INSTALLED`.

The descriptor remains in the registry (read-only). To
unregister, the operator deletes the descriptor file and
restarts the backend.

### 9.7 Edition-specific quirks

- CE only supports `runtime_type: docker` (the first driver).
- The `runtime-registry/` directory is included in the CE
  distribution by default (with the Kokoro runtime pre-published
  for ease of use).
- CE default `idle_timeout` is `15m`; CE default
  `RUNTIME_SERVICE_ENABLED` is `False`. Both are operator-
  configurable.
- In CE, if Docker is not installed, the in-process fallback is
  the only path. The `RuntimeManager` reports
  `RuntimeRequirementsNotMet` when the user tries to install
  a runtime without Docker available.

---

## 10. Cloud Edition operations

The Cloud Edition shares the **same Runtime Manager and the same
Runtime Service Contract** with CE. The only difference is the
**driver**: Cloud uses `KubernetesRuntimeDriver` (a separate ADR,
not authored here).

### 10.1 Installation

- The runtime descriptor is uploaded to the Cloud runtime store
  (an S3 bucket, a configmap, or a custom resource — TBD by the
  Cloud ADR).
- The Cloud `RuntimeManager` registers the descriptor.
- A `RuntimeInstance` is created in state `Installed` (no
  container yet).

### 10.2 Activation

- The `KubernetesRuntimeDriver` (separate ADR) creates a
  Deployment with the runtime image, a Service that exposes it,
  and (if `spec.requirements.gpu = required`) a GPU resource
  claim.
- The driver waits for the Service's endpoints to be `Ready`.
- The instance transitions to `Active` when the readiness probe
  succeeds.

### 10.3 Update

- The driver performs a **rolling update**: the existing Pod is
  replaced by a Pod running the new image; the Service shifts
  traffic after the new Pod is ready.
- The Active Artifact is preserved; the runtime re-reads it on
  the next generation.

### 10.4 Removal

- The driver deletes the Deployment, Service, and (when no
  longer referenced) the underlying image from the registry.

### 10.5 Edition-specific quirks

- Cloud supports multiple `runtime_type` values: `docker`
  (legacy / single-tenant), `kubernetes` (multi-tenant default).
- Cloud's `RuntimeManager` selects the driver based on the
  current deployment context. The selection is invisible to
  callers; the surface is uniform.
- Cloud's authentication (the deferred Cloud decision) is added
  by the Cloud ADR; CE's default of `none` is unchanged.

---

## Components touched

### Backend (new components in Phase 2 implementation)

| Component | Sub-phase | Role |
|---|---|---|
| `RuntimeDescriptor` (Pydantic) | 2A | Schema + validation for `runtime.yaml`. |
| `RuntimeRegistry` | 2A | File-based discovery, indexes, lookup. |
| `RuntimeManager` | 2A | Orchestration; resolution; lifecycle delegation. |
| `RuntimeDriver` (Protocol) | 2A | Substrate abstraction. |
| `DockerRuntimeDriver` | 2B | First concrete driver. |
| `RuntimeEndpointResolver` | 2A | (Part of RuntimeManager; named separately for clarity.) |
| `RuntimeEventBus` | 2A | Structured events; subscribes to the existing `app.core.events` channel. |
| `RuntimeInstance` (frozen dataclass) | 2A | In-memory state. |
| `HTTPTransport` | 2C | Generic HTTP client for adapters. |
| `KokoroAdapter` (modified) | 2C | Adds `KOKORO_RUNTIME_URL` path. |
| `lint_no_docker_outside_driver` | 2B | AST check banning `import docker` outside the driver. |

### Backend (no changes in Phase 2 implementation)

- `PeakVoxRuntime` (`backend/app/services/runtime.py`) — contract
  unchanged; internally it may gain a call to
  `RuntimeManager.resolve(model_id)`.
- `ModelAdapter` contract — unchanged.
- All other adapters — unchanged (OmniVoice, Fish continue
  in-process until Phases 5-6).
- All domain repositories, services, and APIs — unchanged in this
  phase. **No new API endpoints are added in this ADR.** The
  `GET /api/v1/runtimes` endpoint is a Phase 3+ concern (or
  earlier if needed for ops visibility).

### Frontend (no changes in this phase)

A future Models page may surface runtime install/activate/deactivate
UI, but that is a UX decision deferred to a later phase. The
`voices/page.tsx` UI is not touched.

---

## Data / schema changes

**None in this ADR.** Per Constitution §18, any persistence
introduced by Phase 2 implementation will follow the SQLite-safe
runner in `app/core/migrations.py`. A possible `runtime_instances`
table (infrastructure state, not domain) is **deferred** to a later
phase. ADR-0017 deliberately does not introduce it; the in-memory
cache in `RuntimeManager` is sufficient for Phase 2.

---

## Capability / edition gating

- **ADR-0003** — Capabilities remain declared on `ModelDescriptor`;
  the RuntimeDescriptor's `spec.capabilities` is a subset and is
  validated against the model at load time.
- **ADR-0005** — Model editions (CE / Cloud) remain declared on
  the model. The RuntimeDescriptor's `metadata.edition` and
  `spec.requirements.edition` refine the deployment.
- **ADR-0012** — Voice resources and creation sources are
  unchanged.

---

## Constrained by ADRs

- **ADR-0016** — High-level Runtime-Service architecture. ADR-0017
  is the implementation architecture. Where ADR-0016 defers,
  ADR-0017 commits (and `OPEN_DECISIONS.md` Decision 10 is
  resolved).
- **ADR-0004** — Voice / Variant / Model separation. Adapters
  remain the only translation point.
- **ADR-0006, ADR-0008, ADR-0009** — Variant realization + artifact
  lifecycle. Not bypassed.
- **ADR-0010, ADR-0011, ADR-0012** — Provisioning policies,
  creation sources, identity/catalog separation. Not bypassed.
- **ADR-0001, ADR-0002, ADR-0003, ADR-0005, ADR-0007** — Voice
  identity, model catalog, capability contract, edition gating,
  canonical metadata. Unchanged.

**No ADR is superseded.** ADR-0017 is additive.

---

## Constitution alignment

ADR-0017 *strengthens* (never weakens):

- **Article I, §1** — Universal Voice Runtime, not a model frontend.
- **Article III, §8** — The Runtime is the single, model-agnostic
  generation entry point. The Runtime Manager is the only thing
  the API talks to for runtime resolution.
- **Article III, §9** — Nothing above the adapter line imports a
  model implementation. The line is now drawn around the *backend
  process and the Runtime Manager*. The `DockerRuntimeDriver` is
  *below* the line (it imports Docker SDK, not model code).
- **Article V, §14–17** — CE and Cloud share the architecture. The
  RuntimeDriver is the seam.
- **Article VI, §18** — Additive and idempotent migrations. No
  schema changes in this ADR; future persistence is additive.

No exception to the constitution is introduced.

---

## Risks

| Risk | Mitigation |
|---|---|
| `RuntimeDescriptor` schema evolves breaking. | `api_version` is part of the schema; future versions are additive within a major; breaking changes get a new `api_version`. |
| `DockerRuntimeDriver` leaks substrate details. | ADR pins the protocol; the manager never imports Docker; the `lint_no_docker_outside_driver` AST check enforces this. |
| Endpoint resolution races during lazy activation. | Single in-process lock around the `(runtime_id → RuntimeInstance)` cache. |
| Runtime service contract drifts across providers. | The contract is the same 5 endpoints for every model. Provider-specific endpoints are forbidden at the contract level; if needed, they live under `/v1/models/<model_id>/...`. |
| Kokoro migration breaks existing CE users. | Migration is additive and env-gated. In-process fallback is the default. Unset `KOKORO_RUNTIME_URL` to roll back. |
| In-memory cache lost on backend restart. | Explicit Phase 2 design; runtimes must be re-activated. A future ADR adds persistence (OPEN_DECISIONS Decision 12+). |
| Error mapping between driver and API is inconsistent. | The driver raises typed `RuntimeDriverError` subclasses; the manager translates them deterministically into the canonical error body (§6.6). |

---

**Related:** [`SPEC.md`](./SPEC.md) · [`TASKS.md`](./TASKS.md) ·
[`VALIDATION.md`](./VALIDATION.md) · [`STATUS.md`](./STATUS.md) ·
[`adr-0017-runtime-services-implementation.md`](../../../DECISIONS/adr-0017-runtime-services-implementation.md) ·
[`adr-0016-models-as-runtime-services.md`](../../../DECISIONS/adr-0016-models-as-runtime-services.md) ·
[`../../ARCHITECTURE/runtime-architecture.md`](../../../ARCHITECTURE/runtime-architecture.md)
