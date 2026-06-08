# STATUS — Runtime Services Implementation (Phase 2 ADR + Phase 3)

Lifecycle position in the SDD flow:
`Brainstorm → Specification → Design → Tasks → Implementation → Validation → Review → Merge`

- **Current stage:** Phase 3 IN PROGRESS (post-Phase-2 audit,
  post-refinements R1–R8).
- **ADR status:** **ACCEPTED (refined)** — ADR-0017 Accepted
  2026-06-07; refined 2026-06-08 with 8 post-audit refinements
  (R1 self-contained entries, R2 `spec.build`, R3
  `RUNTIME_SERVICE_ENABLED`, R4 runtime-first lifecycle, R5
  Phase 3 DoD, R6 lazy startup, R7 idle reaper, R8 reference
  pattern).
- **Implementation status:** Phase 2 IMPLEMENTED (2A+2B+2C+2D);
  Phase 3 IN PROGRESS (P1–P9 tasks defined in
  [`TASKS.md`](./TASKS.md) § Phase 3).
- **Architecture review:** Runtime Activation Audit PASSED
  (all 7 checks); Runtime Service Readiness Audit PASSED
  (architecture correct; runtime service missing). The 8
  refinements address the readiness audit's findings.
- **Owner / last update:** 2026-06-08.

---

## Sub-phase status

### Phase 2 (complete)

| Sub-phase | Scope | Status | Notes |
|---|---|---|---|
| 2A | Foundations: Descriptor, Registry, Manager, Driver protocol, RuntimeInstance, events | **IMPLEMENTED** | 9 modules + 9 test files. Commits `06e1007`–`e0022fc`. |
| 2B | First driver: `DockerRuntimeDriver` + `lint_no_docker_outside_driver.py` | **IMPLEMENTED** | `DockerRuntimeDriver` (21 tests), lint script (8 tests), manager wiring (11 tests). Commits `d76d330`–`4aef672`. |
| 2C | Service contract + `KokoroAdapter` integration (`KOKORO_RUNTIME_URL` path) | **IMPLEMENTED** | `HTTPTransport` (14 tests) + `KokoroAdapter` integration (8 tests) + `Settings.KOKORO_RUNTIME_URL` (3 tests) + gated E2E (1 skipped). Commits `7128cc1`–`9c01eea`. |
| 2D | CE operations: install / activate / update / remove; runtime-registry/ with Kokoro descriptor; bridge activation; CLI skeleton | **IMPLEMENTED** | Manager operations (12 tests), bridge activation (5 tests), CLI skeleton (4 tests), descriptor publish (11 tests). Commits `e5be62b`–`6c78e2e`. |
| 2 — Audit | Runtime Activation Audit | **PASSED** | All 7 invariant checks PASS. Commit `7da412a`. |

### Phase 3 (in progress)

| Task | Scope | Status | Notes |
|---|---|---|---|
| Refinements R1–R8 applied to ADR / SPEC / DESIGN / TASKS / VALIDATION | 2026-06-08 | IN PROGRESS | Doc updates landing; code changes (Settings.RUNTIME_SERVICE_ENABLED, RuntimeBuild Pydantic, idle_timeout in RuntimeLifecycle) landing in this commit. |
| **P1** | Build `peakvox/kokoro-runtime` (descriptor + Dockerfile + server.py + requirements.txt + README.md + tests/) | NOT_STARTED | Depends on refinements. |
| **P2** | Wire `RuntimeRegistry` at backend startup (gated on `RUNTIME_SERVICE_ENABLED`) | NOT_STARTED | Depends on P1. |
| **P3** | Wire `RuntimeManager` idle reaper (R7) | NOT_STARTED | Depends on P2. |
| **P4** | Connect Models page operations to `RuntimeManager` (R4) | NOT_STARTED | Depends on P3. |
| **P5** | Add `peakvox-kokoro-runtime` to `docker-compose.yml` | NOT_STARTED | Depends on P1. |
| **P6** | Execute real E2E generation through runtime service | NOT_STARTED | Depends on P4, P5. |
| **P7** | Provider validation G6 (contract) + G7 (performance) + G8 (error recovery) + G9 (idle reaper) + G10 (backend without Kokoro) | NOT_STARTED | Depends on P6. |
| **P8** | Validate backend container starts without `kokoro` installed (R5) | NOT_STARTED | Depends on P7. |
| **P9** | Update state files (IMPLEMENTATION_STATUS, PROJECT_STATE, etc.) | NOT_STARTED | Final task. |

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

## Architectural invariants (recap; 21)

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
16. **A Runtime Registry entry is self-contained** — descriptor,
    Dockerfile, source, requirements, README, tests. A
    descriptor alone is not a valid entry.
17. **The Manager is image-agnostic** — it never sees the
    `spec.build` block; build is a pre-flight concern of the
    registry loader.
18. **Activation is gated on `RUNTIME_SERVICE_ENABLED`** — the
    runtime subsystem is opt-in at startup.
19. **The backend boots with no runtimes active** — lazy
    activation; no runtime container is started at boot.
20. **Runtimes auto-stop after `idle_timeout` of inactivity** —
    the manager owns the idle timer; the container is not torn
    down on every request.
21. **Every new runtime mirrors the Kokoro reference shape** —
    no asymmetric runtime directories in the registry.

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
