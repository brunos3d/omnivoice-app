# STATUS — Runtime Services Implementation (Phase 2 ADR)

Lifecycle position in the SDD flow:
`Brainstorm → Specification → Design → Tasks → Implementation → Validation → Review → Merge`

- **Current stage:** ADR Accepted (architecture only; implementation
  deferred to Phase 2 sub-phases 2A-2D).
- **Implementation status:** **APPROVED** (ADR-0017 Accepted 2026-06-07;
  per Constitution §22, "Accepted" is not "Implemented").
- **Owner / last update:** 2026-06-07.
- **Architecture review:** 0 blocking issues; non-blocking suggestions
  applied (Runtime Persistence → `OPEN_DECISIONS.md` Decision 12;
  ADR_INDEX/IMPLEMENTATION_STATUS consistency fixed).
- **Outcome (on completion of this phase):** ADR-0017 is recorded in
  [`ADR_INDEX.md`](../../../DECISIONS/ADR_INDEX.md) and
  [`IMPLEMENTATION_STATUS.md`](../../../IMPLEMENTATION_STATUS.md).
  `OPEN_DECISIONS.md` Decision 10 is RESOLVED. State files reflect
  the new ADR. No code, no migrations, no `runtime-registry/`
  directory, no `RuntimeManager` class, no `RuntimeDriver` class, no
  `RuntimeDescriptor` class, no new API endpoints, no Docker
  integration, no Kokoro migration code — all deferred to Phase 2
  implementation sub-phases 2A-2D.

---

## Sub-phase status

| Sub-phase | Scope | Status | Notes |
|---|---|---|---|
| 2A | Foundations: Descriptor, Registry, Manager, Driver protocol, RuntimeInstance, events | NOT_STARTED | Awaiting ADR-0017 accept. |
| 2B | First driver: `DockerRuntimeDriver` + `lint_no_docker_outside_driver.py` | NOT_STARTED | Depends on 2A. |
| 2C | Service contract + `KokoroAdapter` integration (`KOKORO_RUNTIME_URL` path) | NOT_STARTED | Depends on 2B. |
| 2D | CE operations: install / activate / update / remove; runtime-registry/ with Kokoro descriptor | NOT_STARTED | Depends on 2C. |

---

## What this phase produced

- [`SPEC.md`](./SPEC.md) — 10 deliverables as Requirements; 15
  acceptance criteria; 15 architectural invariants (12 carried
  from ADR-0016 + 3 new for this ADR).
- [`DESIGN.md`](./DESIGN.md) — the meat: descriptor schema,
  registry model, manager responsibilities and boundaries,
  driver protocol with 10 operations and 4 error-mapping
  categories, Docker driver responsibilities and boundaries,
  the full Runtime Service Contract (5 endpoints, request and
  response shapes, error body), the complete routing flow with
  failure handling, the Kokoro migration plan (4-step rollout
  + declarative rollback), the CE operations, and the Cloud
  operations.
- [`TASKS.md`](./TASKS.md) — 4 sub-phases, TDD per task; explicit
  "do not start until ADR-0017 is accepted" guardrail.
- [`VALIDATION.md`](./VALIDATION.md) — architecture vs provider
  validation distinction preserved for every sub-phase.
- [`STATUS.md`](./STATUS.md) — this file.
- [`adr-0017-runtime-services-implementation.md`](../../../DECISIONS/adr-0017-runtime-services-implementation.md) — the ADR.

## What this phase did NOT produce (per the non-goals)

- No `RuntimeManager` class.
- No `RuntimeDriver` / `DockerRuntimeDriver` class.
- No `RuntimeDescriptor` Pydantic class.
- No `RuntimeRegistry` class.
- No `runtime-registry/` directory.
- No `HTTPTransport` class.
- No `KokoroAdapter` modification.
- No `KOKORO_RUNTIME_URL` plumbing.
- No new API endpoints (e.g. `GET /api/v1/runtimes`).
- No Docker integration / no `import docker` / no
  `docker compose` files.
- No schema changes of any kind.
- No F5-TTS, Fish, XTTS, or any other model migration.
- No `peakvox/kokoro-runtime` image.
- No frontend changes.

---

## Architectural invariants (recap; 15)

1. Models are catalog entities.
2. Runtimes are deployment units.
3. PeakVox installs runtimes, not models. One Model → many
   Runtimes.
4. The backend never owns model dependencies.
5. The backend never executes model inference.
6. **Runtime Manager performs orchestration only**
   (discovers, resolves endpoints, delegates lifecycle, reports
   status).
7. Runtime Registry describes; the descriptor is the contract.
8. Adapters communicate with runtime services; they never talk
   to Docker / Kubernetes / Podman.
9. Runtime services are replaceable.
10. CE and Cloud share the architecture (RuntimeDriver is the
    seam).
11. Runtime infrastructure is not a domain concept.
12. Active Artifact resolution is preserved.
13. **The RuntimeDriver protocol is substrate-neutral** — the
    same interface drives Docker in CE and Kubernetes in Cloud.
14. **The Runtime Service Contract is model-neutral** — every
    Runtime Service exposes the same five endpoints; model-
    specific concerns are routed through metadata.
15. **The migration is additive** — the in-process path remains
    available for every model until Phase 7 explicitly removes
    it.

---

## Phase 2 guardrail (mirrored in NEXT_TASK.md and ROADMAP/CURRENT_PHASE.md)

> **Phase 2 implementation may not begin until ADR-0017 is
> Accepted.** Until then: no `RuntimeManager`, no
> `RuntimeDriver`, no `RuntimeDescriptor`, no `runtime-registry/`,
> no `HTTPTransport`, no `KokoroAdapter` modification, no new API
> endpoints, no Docker integration, no Kokoro migration code.

## What ADR-0017 commits that ADR-0016 deferred

ADR-0016 explicitly deferred 5 open questions to a Phase 2
implementation ADR. ADR-0017 commits them as **accepted
architecture**:

| Open question (Decision 10) | Resolution (ADR-0017) |
|---|---|
| Runtime endpoint discovery | `RuntimeManager.resolve` is the single point; selection rules in DESIGN §3.4; lazy activation by default. |
| Runtime upgrade / rollback | Versioned images; `spec.image.digest` for pinning; no in-place mutable upgrades; rollback = descriptor change. |
| GPU allocation ownership | Runtime Service owns the device; backend never imports CUDA; RuntimeManager only observes capability and health. |
| Runtime health contract | Separate liveness (`/health`) and readiness (`/ready`); readiness must indicate the runtime can actually serve inference; the manager refuses to route to a not-ready instance. |
| Backend-to-runtime authentication | CE default = none; Cloud deferred to the Cloud ADR. `HTTPTransport` accepts an optional bearer token. |

On ADR-0017 accept, `OPEN_DECISIONS.md` Decision 10 is marked
**RESOLVED** and the "Implementation direction (non-binding)"
notes become **accepted architecture** by reference to this ADR.

---

## Next step

On ADR-0017 accept:

1. Mark `OPEN_DECISIONS.md` Decision 10 as **RESOLVED**.
2. Update `NEXT_TASK.md` to promote sub-phase **2A — Foundations**
   as the next P0 work item (still gated on writing the Phase 2
   sub-phase implementation plan; the four sub-phases have their
   own breakdown here in `TASKS.md`).
3. Begin sub-phase 2A when ready (TDD-shaped tasks in
   `TASKS.md` §2A).
4. Update `IMPLEMENTATION_STATUS.md` to add 2A's components at
   status IN_PROGRESS.

Phase 2 implementation does not start until ADR-0017 is Accepted.
**No exceptions.**

---

**Related:** [`SPEC.md`](./SPEC.md) · [`DESIGN.md`](./DESIGN.md) ·
[`TASKS.md`](./TASKS.md) · [`VALIDATION.md`](./VALIDATION.md) ·
[`adr-0017-runtime-services-implementation.md`](../../../DECISIONS/adr-0017-runtime-services-implementation.md) ·
[`adr-0016-models-as-runtime-services.md`](../../../DECISIONS/adr-0016-models-as-runtime-services.md)
