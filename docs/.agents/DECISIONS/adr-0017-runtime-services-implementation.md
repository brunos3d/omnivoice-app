# ADR-0017: Runtime Services Implementation (Phase 2 Implementation ADR)

- **Status:** Accepted (refined 2026-06-08)
- **Date:** 2026-06-07 (refined 2026-06-08)
- **Deciders:** PeakVox architecture.
- **Supersedes:** none.
- **Superseded by:** none.
- **Spec:** [`../SPECS/FEATURES/runtime-services-implementation/`](../SPECS/FEATURES/runtime-services-implementation/)
- **Parent:** [`adr-0016-models-as-runtime-services.md`](adr-0016-models-as-runtime-services.md) (Accepted)

---

## Context

ADR-0016 (Models as Runtime Services) is **Accepted** and committed
(2026-06-07, SHA `feb4fd3`). It defines the high-level Runtime-
Service architecture — Runtime Registry, Runtime Manager, Runtime
Driver, Runtime Service — and is explicit that **Phase 2
implementation cannot begin until a Phase 2 implementation ADR is
Accepted** that addresses five deferred open questions
([`OPEN_DECISIONS.md` Decision 10](../OPEN_DECISIONS.md)):

1. Runtime endpoint discovery
2. Runtime upgrade / rollback
3. GPU allocation ownership
4. Runtime health contract
5. Backend-to-runtime authentication

The five questions are seeded with "Implementation direction
(non-binding)" notes in OPEN_DECISIONS Decision 10. They become
binding only when committed by an Accepted ADR.

Additionally, the implementation architecture needs the rest of
the Phase 2 surface to be specified: the descriptor schema, the
registry model, the manager's orchestration and resolution flows,
the driver protocol and error contract, the wire contract of the
Runtime Service, the routing lifecycle, the Kokoro migration plan,
and the edition-specific install/activate/update/remove
operations.

The intended outcome is: **"Phase 2 may begin safely."**

---

## Options considered

### Option A — Begin implementation on the non-binding direction notes

Treat the "Implementation direction (non-binding)" notes in
`OPEN_DECISIONS.md` Decision 10 as sufficient and start writing
code.

- **Pros:** Minimum process overhead; faster start.
- **Cons:** The notes are *explicitly* non-binding. Implementation
  on non-binding direction is implementation on unaccepted
  architecture — a constitutional violation. The next ADR would
  have to ratify decisions that are already half-implemented, a
  textbook sunk-cost trap. The notes are also incomplete; they
  cover the five open questions but do not address the descriptor
  schema, the registry model, the service contract, the routing
  flow, the Kokoro migration, or the edition operations.
- **Rejected.**

### Option B — Just-in-time decisioning during implementation

Resolve each open question on the fly, as the implementer reaches
it.

- **Pros:** Decisions are made in context.
- **Cons:** Each decision is invisible to the rest of the team
  until the commit lands. Architectural drift is the default
  outcome. Review happens after the fact, when rework is
  expensive. The five-question decision surface and the rest of
  the Phase 2 surface all need consistent architecture; piecemeal
  decisioning makes that hard.
- **Rejected.**

### Option C — Formal Phase 2 Implementation ADR (chosen)

Write a dedicated ADR that commits the five open questions *and*
specifies the rest of the Phase 2 surface (descriptor, registry,
manager, driver, Docker driver, service contract, routing,
Kokoro migration, CE/Cloud operations) as a single coherent
architecture. The ADR is the gating step before any Phase 2
implementation work.

- **Pros:**
  - **Single review surface.** The architecture is reviewed once,
    as a whole; implementation work can begin immediately after
    accept.
  - **Constitution §22 alignment.** An Accepted ADR is not
    evidence of implementation, but it is the architectural
    baseline. Implementation tasks reference the ADR by path
    (per AGENTS.md "Implementation Rule").
  - **OPEN_DECISIONS closure.** The five deferred questions
    become accepted architecture; Decision 10 is marked RESOLVED.
  - **TDD-shaped tasks.** Implementation can be drawn directly
    from the architecture with no further design work.
  - **Constitution alignment preserved.** Articles I, III §8,
    III §9, V remain in force; the runtime infrastructure stays
    out of the domain (Article II).

- **Cons:**
  - **More documentation up front.** This ADR is larger than
    ADR-0016 because it specifies 10 components in detail.
    Mitigation: the design is split across
    `SPEC.md`/`DESIGN.md`/`TASKS.md`/`VALIDATION.md`/`STATUS.md`
    for navigability; the ADR itself stays focused on context,
    options, decision, and consequences.

- **Chosen.**

---

## Decision

PeakVox adopts the **Runtime Services Implementation
Architecture** defined by this ADR and its companion spec
([`SPEC.md`](../SPECS/FEATURES/runtime-services-implementation/SPEC.md),
[`DESIGN.md`](../SPECS/FEATURES/runtime-services-implementation/DESIGN.md),
[`TASKS.md`](../SPECS/FEATURES/runtime-services-implementation/TASKS.md),
[`VALIDATION.md`](../SPECS/FEATURES/runtime-services-implementation/VALIDATION.md),
[`STATUS.md`](../SPECS/FEATURES/runtime-services-implementation/STATUS.md)).

The change is purely architectural in this phase. **No code is
written.** The 10 deliverables (the surface for Phase 2
implementation) are specified as architecture, not as
implementation. Implementation begins in Phase 2 sub-phases
2A-2D after this ADR is Accepted.

### 10 deliverables

1. **RuntimeDescriptor** — schema, identity rules, runtime
   metadata, versioning, runtime capabilities, runtime
   requirements. See
   [DESIGN §1](../SPECS/FEATURES/runtime-services-implementation/DESIGN.md#1-runtimedescriptor).

2. **RuntimeRegistry** — file-based discovery, descriptor loading,
   in-memory indexes, lookup, lifecycle visibility. See
   [DESIGN §2](../SPECS/FEATURES/runtime-services-implementation/DESIGN.md#2-runtimeregistry).

3. **RuntimeManager** — orchestration only (canonical phrasing
   from ADR-0016: discovers, resolves endpoints, delegates
   lifecycle, reports status; never executes, allocates GPUs,
   loads weights, imports frameworks, performs substrate-specific
   operations). Orchestration flow and resolution flow specified.
   See
   [DESIGN §3](../SPECS/FEATURES/runtime-services-implementation/DESIGN.md#3-runtimemanager).

4. **RuntimeDriver** — formal `Protocol`; the 10 normative
   operations (install, update, remove, start, stop, restart,
   status, logs, health, metrics); 8 error categories; retry and
   timeout policy. See
   [DESIGN §4](../SPECS/FEATURES/runtime-services-implementation/DESIGN.md#4-runtimedriver).

5. **DockerRuntimeDriver** — first concrete driver; implement
   the protocol against the Docker Engine API; boundaries on
   K8s, Podman, remote hosts, networks, volumes, privileges. See
   [DESIGN §5](../SPECS/FEATURES/runtime-services-implementation/DESIGN.md#5-dockerruntimedriver).

6. **Runtime Service Contract** — 5 HTTP/JSON endpoints every
   Runtime Service MUST expose: `/health` (liveness), `/ready`
   (readiness), `POST /v1/generate` (inference),
   `POST /v1/variants/build` (variant build),
   `GET /v1/metadata` (capabilities). Canonical error body
   shape. See
   [DESIGN §6](../SPECS/FEATURES/runtime-services-implementation/DESIGN.md#6-runtime-service-contract).

7. **Runtime Routing** — full request lifecycle from
   `PeakVoxRuntime.generate` through the `RuntimeManager` to the
   Runtime Service and back, with a 12-step flow and a failure
   matrix. See
   [DESIGN §7](../SPECS/FEATURES/runtime-services-implementation/DESIGN.md#7-runtime-routing).

8. **Kokoro Migration** — current state (in-process adapter),
   target state (HTTP runtime service), 4-step additive migration
   strategy, declarative rollback (`KOKORO_RUNTIME_URL` env
   var), no schema changes. See
   [DESIGN §8](../SPECS/FEATURES/runtime-services-implementation/DESIGN.md#8-kokoro-migration).

9. **Community Edition operations** — install / activate / update
   / remove; the `DockerRuntimeDriver` provides the substrate;
   the in-process fallback remains for users without Docker.
   See
   [DESIGN §9](../SPECS/FEATURES/runtime-services-implementation/DESIGN.md#9-community-edition-operations).

10. **Cloud Edition operations** — install / activate / update /
    remove at the manager level; the `KubernetesRuntimeDriver` is
    a separate ADR. See
    [DESIGN §10](../SPECS/FEATURES/runtime-services-implementation/DESIGN.md#10-cloud-edition-operations).

### Architectural flow (preserved from ADR-0016)

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

The Active Artifact resolution step is **mandatory** and **may
not be bypassed**.

### The five deferred open questions — resolved

| Open question (Decision 10) | Resolution (this ADR) |
|---|---|
| Runtime endpoint discovery | `RuntimeManager.resolve` is the single resolution point. Selection rules: edition filter → default → priority → hint → first match. Lazy activation by default; first resolve call triggers `start_runtime` if needed. |
| Runtime upgrade / rollback | Versioned images. `spec.image.digest` is the immutable pin. No in-place mutable upgrades. Rollback is a descriptor change (point to a prior tag); no hot-swap. |
| GPU allocation ownership | Runtime Service owns the device. Backend never imports CUDA. `RuntimeManager` only observes capability and reports health; it does not allocate, schedule, or release GPUs. |
| Runtime health contract | Separate liveness (`GET /health`) and readiness (`GET /ready`). Readiness must indicate the runtime can actually serve inference (model loaded, weights resident, device claimed, no transient error). `RuntimeManager` refuses to route to a not-ready instance. |
| Backend-to-runtime authentication | CE default = `none`. The `HTTPTransport` accepts an optional bearer token; CE does not set one. Cloud's choice (token / mTLS / sidecar) is deferred to the Cloud ADR; the protocol supports either. |

### Domain boundary (preserved from ADR-0016)

Runtime infrastructure is **not** part of the domain model. The
domain model contains: Voice, VoiceSourceAsset, VoicePreview,
VoiceVariant, VoiceVariantArtifact, Model, Provider, Adapter,
VoiceResource.

Runtime infrastructure (RuntimeRegistry, RuntimeManager,
RuntimeDriver, RuntimeService, RuntimeInstance) is **infrastructure
only** and must never become a domain entity.

**Forbidden future patterns** (carried from ADR-0016):

- `RuntimeServiceEntity`
- `RuntimeServiceRepository`
- `RuntimeVariant`
- `RuntimeArtifact`
- Any `*Entity` / `*Repository` that names a runtime concept

### Migration phases (carried from ADR-0016)

ADR-0017 does not change the phase plan. Phase 2 implementation
begins after this ADR is Accepted.

1. **Phase 1** — ADR + design docs. ✅ Complete (ADR-0016,
   2026-06-07).
2. **Phase 2** — Runtime Registry + Runtime Manager skeleton +
   `DockerRuntimeDriver`. **Begins on ADR-0017 accept.**
3. **Phase 3** — Kokoro migration. First validation target.
4. **Phase 4** — F5-TTS as Runtime Service. Reference
   implementation.
5. **Phase 5** — Fish Audio migration.
6. **Phase 6** — OmniVoice migration.
7. **Phase 7** — Remove direct in-process model execution.
   Backend image becomes model-free.

### Constitutional reinforcement

This ADR *strengthens* (never weakens):

- **Article I, §1** — Universal Voice Runtime, not a model
  frontend.
- **Article III, §8** — The Runtime is the single, model-agnostic
  generation entry point.
- **Article III, §9** — Nothing above the adapter line imports a
  model implementation. The line is now drawn around the backend
  process and the `RuntimeManager`. The `DockerRuntimeDriver`
  imports the Docker SDK; only the Runtime Service imports the
  model.
- **Article V, §14–17** — CE and Cloud share the architecture.
  The `RuntimeDriver` is the seam.
- **Article VI, §18** — Migrations are additive and idempotent.
  This ADR introduces no schema changes; future persistence is
  additive via the SQLite-safe runner.

No exception to the constitution is introduced.

### Refinements (2026-06-08, post-Phase-2 audit)

The Runtime Service Readiness Audit
([`AUDITS/runtime-service-readiness-audit.md`](../VALIDATION/AUDITS/runtime-service-readiness-audit.md))
confirmed Phase 2 produced the runtime infrastructure but did not
yet deliver a concrete runtime service. Five refinements were
applied to make Phase 3 implementable. None of them contradict the
original decision; all are clarifications or extensions.

**R1. Registry structure — self-contained entries.**

Each `runtime-registry/<runtime_id>/` entry is now required to be
**self-contained** (build + run + validate + publish from one
directory). A descriptor alone is not sufficient; the entry must
include the source necessary to build the image it describes.

```
runtime-registry/
└── <runtime_id>/
    ├── descriptor.json       (the contract)
    ├── Dockerfile            (CE build)
    ├── server.py             (CE entrypoint)
    ├── requirements.txt      (CE runtime deps)
    ├── README.md             (operator documentation)
    └── tests/                (CE validation)
```

This becomes the reference shape for every runtime added in the
future: F5-TTS, XTTS, OpenVoice, Fish, OmniVoice, etc.

**R2. Descriptor enhancement — `spec.build` block.**

Today the descriptor only declared a prebuilt OCI image
(`spec.image.repository` + `spec.image.tag`). To support both
local builds (CE) and prebuilt images (Cloud) without changing
`RuntimeManager` behavior, a new optional block is added:

```json
"spec": {
  "image": { "repository": "peakvox/kokoro-runtime", "tag": "0.1.0" },
  "build": {
    "entrypoint": "server.py",
    "build_context": ".",
    "dockerfile": "Dockerfile"
  },
  "service": { ... },
  ...
}
```

- CE: descriptor carries `build`; a build script reads it, builds
  the image, updates `spec.image.digest` to the local-build sha,
  and proceeds with run.
- Cloud: descriptor omits `build`; `spec.image` is a published
  image in a registry.
- `RuntimeManager` is **image-agnostic**. It only ever looks at
  `spec.image`; the `build` block is a pre-flight concern of the
  registry loader / build script, never of the manager.

**R3. `RuntimeManager` activation rule — `RUNTIME_SERVICE_ENABLED`.**

`KOKORO_RUNTIME_URL` is **adapter configuration** (data plane —
where the adapter sends HTTP requests). It is **not** infrastructure
configuration (control plane — whether the backend wires up the
runtime subsystem at all).

A new `Settings.RUNTIME_SERVICE_ENABLED: bool = False` is introduced
(CE default off, Cloud default true, future). Backend startup wires
up `RuntimeRegistry` + `RuntimeManager` + `DockerRuntimeDriver` only
when this flag is true. The manager remains completely
**provider-agnostic** — it must not know about Kokoro, F5-TTS,
XTTS, OpenVoice, or Fish Audio.

**R4. Model lifecycle direction — runtime first, model status derived.**

The Model is a **catalog entity**. The Runtime is the **operational
entity**. Model status must reflect runtime state, not the other
way around.

Lifecycle direction:

```
Install Runtime
  → Pull / build runtime image
    → Install runtime
      → Activate runtime
        → Runtime Ready
          → Update Model Status (derived from runtime state)
```

The Models page "Install Model" / "Activate Model" actions delegate
to `RuntimeManager.install(runtime_id)` /
`RuntimeManager.activate(runtime_id)`. The model id is resolved to
the default `runtime_id` via the registry (`is_default = true`,
highest `priority`). The model row's `status` column is updated
**after** the runtime transition succeeds. Runtime state does not
reflect model state; model state reflects runtime state. A runtime
can exist without a model (rare, future); a model cannot be
"active" without a runtime.

**R5. Phase 3 Definition of Done — backend without Kokoro.**

The strongest architectural proof is:

> The backend container must start successfully with Kokoro
> completely removed from the backend Python environment.
> Voice generation must still succeed through the Runtime Service.

This is the test that **the backend is orchestration and the
runtime container is the inference engine**. The runtime container
owns weights, model packages, inference framework, and runtime
dependencies. The backend owns none of them. This invariant
becomes a Phase 3 acceptance gate (see
[`VALIDATION.md`](../SPECS/FEATURES/runtime-services-implementation/VALIDATION.md)
§ Phase 3 DoD).

**R6. Lazy startup — no runtimes active at backend boot.**

The backend boots with **zero active runtimes**. Runtimes activate
on first `RuntimeManager.resolve(model_id)` call. The wrong
shape — start Kokoro, OmniVoice, F5, XTTS, OpenVoice all at boot
— does not scale (resource waste, slow boot, GPU contention).
The correct shape is: boot fast, lazy activation on first use,
idle timeout frees resources when no one is calling.

This is consistent with ADR-0017 §3.4 (lazy activation by
default); the refinement makes the contract explicit: **at
backend startup, no runtime container is started, and the
RuntimeManager's instance cache is empty**.

**R7. Idle timeout — auto-stop after N minutes of inactivity.**

Stopping a runtime container after every generation is
unacceptable (e.g. 2s startup + 10s model load + 1s inference =
13s for 1s of useful work). Keeping a runtime container
indefinitely is also unacceptable (GPU / VRAM held forever).
The middle ground: **the container stays Active while in use,
and is auto-stopped after a configurable idle timeout**.

```json
"spec": {
  "lifecycle": {
    "install_policy": "pull-on-install",
    "health_interval_seconds": 10,
    "health_timeout_seconds": 3,
    "start_timeout_seconds": 60,
    "restart_policy": "on-failure",
    "idle_timeout": "15m"
  }
}
```

| Edition | Default `idle_timeout` | Rationale |
|---|---|---|
| Community Edition | `15m` | Release GPU/VRAM/RAM after 15 minutes of inactivity; keep CE responsive. |
| Cloud | `never` | The autoscaler / scheduler owns lifecycle. |

Allowed values: `never`, `15m`, `30m`, `1h`, `6h`. The manager
records `last_request_at` on every `resolve()`; a background
task checks idle runtimes and calls `stop_runtime` when the
timeout elapses. On next `resolve()`, the manager
re-activates the runtime (warm or cold start).

**R8. Reference implementation pattern.**

`runtime-registry/kokoro-82m/` is the **canonical shape** for
every future runtime. The directory contains exactly:

```
runtime-registry/kokoro-82m/
├── descriptor.json       (the contract)
├── Dockerfile            (CE build)
├── server.py             (CE entrypoint)
├── requirements.txt      (CE runtime deps)
├── README.md             (operator documentation)
└── tests/                (CE validation)
```

When the next runtime is added (F5-TTS, XTTS, OpenVoice, Fish,
OmniVoice), it copies this shape verbatim and adjusts:

1. `descriptor.json`: `metadata.id`, `metadata.name`,
   `metadata.provider`, `metadata.version`,
   `spec.image.{repository,tag,digest}`,
   `spec.service.{port, paths}`,
   `spec.model_binding.model_id`,
   `spec.build.{entrypoint,build_context,dockerfile}`,
   `spec.requirements.{gpu, min_vram_gb, cpu_cores, memory_gb}`,
   `spec.capabilities` (subset of the bound model),
   `spec.lifecycle.idle_timeout`.
2. `Dockerfile`: change `FROM`, copy the new source, install
   the new `requirements.txt`, expose the new port.
3. `server.py`: implement the 5-endpoint Runtime Service
   Contract (calls into the new framework).
4. `requirements.txt`: pin the new framework.
5. `README.md`: provider-specific operator notes.
6. `tests/`: contract tests + provider-specific unit tests.

**No new runtime ships without a copy of the `kokoro-82m/`
shape.** This is what makes the Runtime Registry a true
catalog of installable runtimes rather than a folder of
asymmetric artifacts.

Kokoro is the only runtime built in Phase 3. F5-TTS, XTTS,
OpenVoice, Fish, OmniVoice are deferred to Phases 4-6 and
must follow the Kokoro reference.

### Architectural invariants (15)

The 12 invariants from ADR-0016, plus 3 new for this ADR:

1. Models are catalog entities.
2. Runtimes are deployment units.
3. PeakVox installs runtimes, not models. One Model → many
   Runtimes.
4. The backend never owns model dependencies.
5. The backend never executes model inference.
6. Runtime Manager performs orchestration only.
7. Runtime Registry describes; the descriptor is the contract.
8. Adapters communicate with runtime services; they never talk
   to Docker / Kubernetes / Podman.
9. Runtime services are replaceable.
10. CE and Cloud share the architecture.
11. Runtime infrastructure is not a domain concept.
12. Active Artifact resolution is preserved.
13. **The RuntimeDriver protocol is substrate-neutral** — the
    same interface drives Docker in CE and Kubernetes in Cloud.
14. **The Runtime Service Contract is model-neutral** — every
    Runtime Service exposes the same five endpoints.
15. **The migration is additive** — the in-process path remains
    available for every model until Phase 7 explicitly removes
    it.

### Final statement

> **Voices are assets. Models are engines. Runtimes are
> infrastructure. Adapters are translators. The Runtime is
> orchestration. The implementation begins now — safely.**

---

## Consequences

### Positive

- **Concrete architecture.** Phase 2 implementation can begin
  immediately on accept; TDD tasks are drawn directly from
  `TASKS.md` without further design work.
- **OPEN_DECISIONS closure.** Decision 10 (the five open
  questions) is resolved by this ADR; the "Implementation
  direction (non-binding)" notes become **accepted
  architecture**.
- **Runtime Service Contract is the same for every model.**
  Future providers (F5-TTS, Fish, XTTS, OpenVoice, etc.) all
  implement the same five endpoints. Model-specific concerns
  are confined to `/v1/models/<id>/...` if needed.
- **Kokoro migration is additive and reversible.** The in-process
  path remains the default. `KOKORO_RUNTIME_URL` opts in to the
  runtime path. Rollback is one environment variable.
- **Edition parity is preserved by construction.** CE and Cloud
  share the manager and the contract; only the driver
  implementation differs.
- **TDD-shaped implementation.** 25+ test files are pre-named
  (`test_runtime_descriptor.py`, `test_docker_runtime_driver.py`,
  `test_kokoro_runtime_adapter.py`, etc.). Each task has a
  failing-test-first shape.
- **Constitution strength.** Articles I, III §8, III §9, V
  become harder to violate, not easier.

### Negative / costs

- **More documentation up front.** This ADR is larger than
  ADR-0016. The design is split across SPEC/DESIGN/TASKS/
  VALIDATION/STATUS for navigability.
- **In-memory cache is volatile.** A backend restart loses the
  RuntimeInstance cache; runtimes must be re-activated. A future
  ADR adds persistence (OPEN_DECISIONS Decision 12+).
- **First-version scope of Docker driver is local only.** Remote
  Docker hosts, custom networks, GPU scheduling beyond the
  default Docker runtime, and other niceties are future ADRs.
- **No new API endpoints in this ADR.** `GET /api/v1/runtimes`
  and friends are Phase 2+ or Phase 3+ depending on UX needs.

### Follow-ups / what this enables or forecloses

- **Enables:** Phase 2 sub-phases 2A-2D. F5-TTS reference
  implementation. Kokoro as a remote runtime. Cloud Edition
  Kubernetes deployment (separate ADR for the driver).
- **Enables:** Backend image shrink (Phase 7's premise). Per-model
  GPU pools. Co-located runtime services in CE for low-latency
  paths. Hot-reload of the Runtime Registry (future ADR).
- **Enables:** A new class of model provider (any process that
  exposes the 5-endpoint contract) integrates without backend
  changes. The 7-phase migration's "add a new model = metadata +
  descriptor + image + adapter" success criterion becomes
  achievable.
- **Forecloses:** Direct in-process model execution as the
  default path for any model with a runtime. The fallback is
  CE-only and explicitly deprecated (Phase 7 removes it).

---

**Related:** [`../SPECS/FEATURES/runtime-services-implementation/`](../SPECS/FEATURES/runtime-services-implementation/) ·
[`adr-0016-models-as-runtime-services.md`](adr-0016-models-as-runtime-services.md) ·
[`../ARCHITECTURE/runtime-architecture.md`](../ARCHITECTURE/runtime-architecture.md) ·
[`../CONSTITUTION.md`](../CONSTITUTION.md) ·
[`../DECISIONS/ADR_INDEX.md`](ADR_INDEX.md) ·
[`../OPEN_DECISIONS.md`](../OPEN_DECISIONS.md) (Decision 10)
