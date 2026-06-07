# SPEC — Runtime Services Implementation (Phase 2 ADR)

> **Status:** PROPOSED (architecture only; implementation deferred to Phase 2 implementation)
> **Date:** 2026-06-07
> **ADR:** [`adr-0017-runtime-services-implementation.md`](../../../DECISIONS/adr-0017-runtime-services-implementation.md)
> **Parent:** [`adr-0016-models-as-runtime-services.md`](../../../DECISIONS/adr-0016-models-as-runtime-services.md) (Accepted)
> **Method:** Architecture documentation. No code, no `RuntimeManager` class, no `RuntimeDriver` class, no `runtime-registry/` directory, no Docker integration, no API endpoints, no Kokoro migration.

---

## Problem

ADR-0016 (Models as Runtime Services) is **Accepted** and committed. It
defines the high-level shape — Runtime Manager, Runtime Driver, Runtime
Service, the substrate-neutral seam — but stops at the architectural
*concept* level. It explicitly defers five open questions to a Phase 2
implementation ADR:

1. Runtime endpoint discovery
2. Runtime upgrade / rollback
3. GPU allocation ownership
4. Runtime health contract
5. Backend-to-runtime authentication

(See [`OPEN_DECISIONS.md` Decision 10](../../../OPEN_DECISIONS.md) for the
seed "Implementation direction (non-binding)" notes.)

The Phase 2 implementation **cannot begin** until those five questions are
resolved *as accepted architecture*, and until the rest of the Phase 2
surface is also specified — the descriptor schema, the registry model,
the driver protocol, the service contract, the routing flow, the Kokoro
migration plan, and the edition-specific install/activate/update/remove
operations. This ADR is that specification.

The intended outcome is: **"Phase 2 may begin safely."**

---

## Goals / Non-goals

### Goals

Translate ADR-0016 into an executable implementation architecture that
answers the 10 deliverables below, in a way that:

- Resolves all five deferred open questions from
  [`OPEN_DECISIONS.md` Decision 10](../../../OPEN_DECISIONS.md).
- Preserves ADR-0016's normalization of the Runtime Manager
  (orchestration only: discovers, resolves endpoints, delegates
  lifecycle, reports status — never executes, never allocates GPUs,
  never loads weights, never imports frameworks, never performs
  substrate-specific operations).
- Preserves the corrected resolution chain
  `Voice → VoiceVariant → Active Artifact → Adapter → Runtime Manager →
  Runtime Driver → Runtime Service → Inference` (ADR-0006/0008/0009
  mandatory; ADR-0016 may not bypass).
- Preserves the domain boundary (runtime infrastructure is not a domain
  concept; forbidden patterns: `RuntimeServiceEntity`,
  `RuntimeServiceRepository`, `RuntimeVariant`, `RuntimeArtifact`).
- Preserves Constitution Articles I, III §8, III §9, V.
- Enables TDD-shaped implementation tasks to be drawn directly from the
  architecture with no further design work.

### Non-goals (this ADR / this phase)

- No code in `backend/` or `frontend/`.
- No `RuntimeManager` class.
- No `RuntimeDriver` / `DockerRuntimeDriver` class.
- No `RuntimeDescriptor` Pydantic class.
- No `runtime-registry/` directory.
- No Docker integration / no `import docker` / no `docker compose`.
- No new API endpoints (e.g. `GET /api/v1/runtimes`).
- No Kokoro migration code. Kokoro continues to execute in-process.
- No adapter changes.
- No schema changes.
- No F5-TTS, Fish, XTTS, or any other model migration.

---

## Requirements

The 10 deliverables (each is a Requirement on this ADR):

### 1. RuntimeDescriptor

Define the descriptor contract — the canonical, declarative description
of a runtime. It must include:

- **Schema** — the full set of fields, types, and validation rules.
- **Identity** — how a runtime is uniquely identified.
- **Runtime metadata** — name, description, provider, version, edition.
- **Versioning** — how a runtime image identity is expressed and pinned
  (image repository + tag + digest).
- **Runtime capabilities** — what the runtime can do (subset of the
  model's `ModelCapabilities`; the runtime cannot exceed the model).
- **Runtime requirements** — what the runtime needs from the host
  (GPU, VRAM, CPU, memory, edition).

### 2. RuntimeRegistry

Define how runtimes are discovered, loaded, looked up, and observed:

- **Discovery model** — where descriptors come from (file-based
  registry on disk for the first driver).
- **Descriptor loading** — how `runtime.yaml` files are parsed,
  validated, and registered.
- **Runtime lookup** — how callers (Runtime Manager, adapters) ask
  "what is the endpoint for runtime X?" or "what runtimes exist for
  model Y?".
- **Runtime lifecycle visibility** — what the registry exposes about
  each runtime's current state (without owning that state).

### 3. RuntimeManager

Define the orchestration component's:

- **Responsibilities** — discovers, resolves endpoints, delegates
  lifecycle, reports status (per ADR-0016 normalization).
- **Boundaries** — what it does NOT own (per ADR-0016 normalization).
- **Orchestration flow** — request → manager → driver → substrate.
- **Runtime resolution flow** — given a `model_id` (and optionally a
  `runtime_hint`), how the manager returns a usable endpoint to the
  adapter.

### 4. RuntimeDriver

Define the substrate abstraction:

- **Protocol** — formal interface, normative operations.
- **Operations** — the same 10 required operations from ADR-0016,
  frozen here as the contract (install, update, remove, start, stop,
  restart, status, logs, health, metrics).
- **Error handling** — error categories, propagation rules, retries,
  timeouts.
- **Lifecycle operations** — install/update/remove semantics; start/
  stop/restart semantics; status/health semantics.

### 5. DockerRuntimeDriver

Define the first concrete driver:

- **Responsibilities** — what it implements on top of Docker.
- **Boundaries** — what it does not do (no K8s, no Podman, no
  local-process); its scope is Docker (and Docker-compatible engines
  with the same SDK surface, like Podman with a Docker-compatible
  socket — not in scope for the first version).

### 6. Runtime Service Contract

Define the wire contract that every Runtime Service MUST expose. Five
endpoints, all over HTTP/JSON in the first version:

- **Health endpoint** — `GET /health` (liveness).
- **Readiness endpoint** — `GET /ready` (can serve inference).
- **Generation endpoint** — `POST /v1/generate` (inference request).
- **Variant build endpoint** — `POST /v1/variants/build` (build a
  variant from a Voice).
- **Metadata endpoint** — `GET /v1/metadata` (capabilities, supported
  languages / tags, realization types, build strategies — what the
  adapter needs to construct a valid request).

### 7. Runtime Routing

Define the complete request lifecycle from the caller down to the
Runtime Service and back, including error handling:

```
Voice
  → VoiceVariant
    → Active Artifact
      → Adapter
        → RuntimeManager.resolve(model_id) → endpoint
          → Adapter.generate(variant, artifact, text, params)
            → RuntimeDriver.request(runtime_id, payload)
              → HTTP POST to Runtime Service
                → Runtime Service executes
                  → Response
```

### 8. Kokoro Migration

Define the migration of Kokoro from in-process to a remote runtime
service:

- **Current state** — in-process adapter; CPU-capable; Apache-2.0;
  82M params; no GPU.
- **Target state** — Kokoro runs in a container; `KokoroAdapter`
  becomes a protocol translator; in-process path remains as a
  fallback for environments without Docker.
- **Migration strategy** — additive; gated by `KOKORO_RUNTIME_URL`;
  feature-flagged per `KokoroAdapter` instance.
- **Rollback strategy** — unset `KOKORO_RUNTIME_URL`; the adapter
  reverts to in-process; no data migration, no schema change.

### 9. Community Edition operations

Define install / activate / update / remove for CE:

- **Installation** — pull image; write descriptor to
  `runtime-registry/<runtime_id>/runtime.yaml`; `RuntimeManager`
  registers the runtime.
- **Activation** — `RuntimeManager` calls
  `RuntimeDriver.start_runtime(runtime_id)`; readiness probe; mark
  instance `Active`.
- **Update** — `RuntimeDriver.update_runtime(runtime_id, descriptor)`
  pulls the new image; existing instances are stopped and recreated
  (no in-place upgrade); Active Artifact is preserved.
- **Removal** — `RuntimeDriver.remove_runtime(runtime_id)` stops the
  instance, removes the image, unregisters the descriptor.

### 10. Cloud Edition operations

Define install / activate / update / remove for Cloud (this ADR only
defines the surface — `KubernetesRuntimeDriver` is a separate ADR):

- **Installation** — submit the runtime descriptor to the Cloud
  runtime store; the `KubernetesRuntimeDriver` (separate ADR)
  creates the Deployment, Service, and (if needed) PVC.
- **Activation** — the driver scales the Deployment to its desired
  replica count; readiness propagates through the Service.
- **Update** — image version bump; the driver performs a rolling
  update.
- **Removal** — the driver deletes the Deployment, Service, and
  (when no longer referenced) the underlying image.

---

## Constraints (constitution articles, ADRs that bind this)

- **Constitution Article I, §1** — Universal Voice Runtime, not a
  model frontend.
- **Constitution Article III, §8** — The Runtime is the single,
  model-agnostic generation entry point.
- **Constitution Article III, §9** — Nothing above the adapter line
  imports a model implementation. ADR-0017 *strengthens* this: the
  Runtime Manager and its drivers must not import torch,
  transformers, kokoro, f5-tts, fish-audio, or any model code.
- **Constitution Article V, §14** — CE and Cloud share the
  architecture. The RuntimeDriver abstraction is the seam.
- **Constitution Article VI, §18** — Migrations are additive and
  idempotent. Any persistence introduced by Phase 2 follows the
  SQLite-safe runner in `app/core/migrations.py`.
- **ADR-0016** — The high-level Runtime-Service architecture. ADR-0017
  is the implementation architecture; it does not contradict
  ADR-0016. Where ADR-0016 defers, ADR-0017 commits.
- **ADR-0004** — Voice / VoiceVariant / Model separation. Adapters
  remain the only translation point.
- **ADR-0006, ADR-0008, ADR-0009** — Variant realization + artifact
  lifecycle. Not bypassed.
- **ADR-0010, ADR-0011, ADR-0012** — Provisioning policies, creation
  sources, identity/catalog separation. Not bypassed.

---

## Acceptance criteria

For this ADR (Phase 2 implementation architecture):

- [ ] ADR-0017 is **Accepted**.
- [ ] All 10 deliverables above are answered as architectural
      specifications, not implementation code.
- [ ] The five open questions from `OPEN_DECISIONS.md` Decision 10
      are resolved as **accepted architecture** (not "implementation
      direction (non-binding)" any more). Decision 10 is marked
      RESOLVED.
- [ ] The RuntimeManager "owns / does NOT" wording matches ADR-0016
      (orchestration only; discovers, resolves endpoints, delegates
      lifecycle, reports status; never executes, allocates GPUs,
      loads weights, imports frameworks, performs substrate-specific
      operations).
- [ ] The Runtime Service Contract is the same for every model
      (5 endpoints, all over HTTP/JSON; the wire shape is uniform;
      models are free to add model-specific endpoints *under*
      `/v1/models/<id>/...` if they need to).
- [ ] The Kokoro migration is **additive** — the in-process path
      remains available until Phase 7 removes it.
- [ ] The CE and Cloud operations (install/activate/update/remove)
      are uniform at the RuntimeManager level; they differ only
      inside the concrete `RuntimeDriver` implementation.
- [ ] `IMPLEMENTATION_STATUS.md` records ADR-0017 as **APPROVED**
      (per Constitution §22, "Accepted" is not "Implemented").
- [ ] `OPEN_DECISIONS.md` Decision 10 is marked **RESOLVED**.
- [ ] No code, no migrations, no `runtime-registry/` directory, no
      `RuntimeManager` class, no `RuntimeDriver` class, no
      `RuntimeDescriptor` Pydantic class, no new API endpoints, no
      Docker integration, no Kokoro migration code. All deferred to
      Phase 2 implementation.

For the broader feature (validated across Phase 2 sub-phases):

- [ ] `RuntimeDescriptor` parses `runtime.yaml` and rejects malformed
      inputs (unit test).
- [ ] `RuntimeRegistry` discovers all runtimes under the configured
      registry path and indexes them by id (unit test).
- [ ] `RuntimeManager` exposes a `resolve(model_id) → endpoint` API
      (unit test with a mock driver).
- [ ] `RuntimeDriver` protocol has structural conformance enforced
      via a `Protocol` check.
- [ ] `DockerRuntimeDriver` install/start/stop/status/health work
      against a mocked Docker client; the manager never imports
      Docker (lint test).
- [ ] `Runtime Service Contract` is exercised by a contract-test
      suite against any conforming service.
- [ ] `KokoroAdapter`, when `KOKORO_RUNTIME_URL` is set, routes all
      traffic through the runtime; when unset, the in-process path
      is used (integration test).
- [ ] Backend image continues to work in the absence of Docker
      (regression test).

---

## Open questions

None. The five open questions from Decision 10 are resolved *by* this
ADR — see [DESIGN.md](./DESIGN.md) for the resolution. Any future
open questions (e.g. Kubernetes driver semantics) get their own ADR
and their own OPEN_DECISIONS entry.

---

## Architectural Invariants (recap; restated for this ADR)

1. Models are catalog entities.
2. Runtimes are deployment units.
3. PeakVox installs runtimes, not models. One Model → many Runtimes.
4. The backend never owns model dependencies.
5. The backend never executes model inference.
6. **Runtime Manager performs orchestration only** (discovers,
   resolves endpoints, delegates lifecycle, reports status).
7. Runtime Registry describes; the descriptor is the contract.
8. Adapters communicate with runtime services; they never talk to
   Docker / Kubernetes / Podman.
9. Runtime services are replaceable.
10. CE and Cloud share the architecture (RuntimeDriver is the seam).
11. Runtime infrastructure is not a domain concept.
12. Active Artifact resolution is preserved.
13. **The RuntimeDriver protocol is substrate-neutral** — the same
    interface drives Docker in CE and Kubernetes in Cloud.
14. **The Runtime Service Contract is model-neutral** — every
    Runtime Service exposes the same five endpoints; model-specific
    concerns are routed through metadata.
15. **The migration is additive** — the in-process path remains
    available for every model until Phase 7 explicitly removes it.

---

## Final Statement

> **Voices are assets. Models are engines. Runtimes are
> infrastructure. Adapters are translators. The Runtime is
> orchestration. The implementation begins now — safely.**

---

**Related:** [`DESIGN.md`](./DESIGN.md) · [`TASKS.md`](./TASKS.md) ·
[`VALIDATION.md`](./VALIDATION.md) · [`STATUS.md`](./STATUS.md) ·
[`adr-0017-runtime-services-implementation.md`](../../../DECISIONS/adr-0017-runtime-services-implementation.md) ·
[`adr-0016-models-as-runtime-services.md`](../../../DECISIONS/adr-0016-models-as-runtime-services.md) ·
[`../../CONSTITUTION.md`](../../../CONSTITUTION.md) ·
[`../../ARCHITECTURE/runtime-architecture.md`](../../../ARCHITECTURE/runtime-architecture.md)
