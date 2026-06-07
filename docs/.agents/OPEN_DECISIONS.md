# OPEN DECISIONS

> Unresolved architectural decisions. When one is resolved, write an ADR (or amend the
> relevant one), then move the entry to [`DECISIONS/ADR_INDEX.md`](DECISIONS/ADR_INDEX.md).
> These mirror the "Candidate future ADRs" in `../architecture/adrs/README.md` plus active
> open questions.

**Last update:** 2026-06-07 (ADR-0017 accepted; Decision 10 RESOLVED; Decision 12 added for Runtime Persistence)

---

## Decision 1 — How to achieve first non-OmniVoice provider validation

- **Status:** ✅ **RESOLVED** (2026-06-05).
- **Decision:** Option 3 — **Kokoro validated as the first non-OmniVoice provider.**
  The `kokoro` pip package was installed (82M, Apache-2.0, CPU-capable), and real audio
  was generated end-to-end through the PeakVox Runtime. All 347 backend tests pass.
- **Context:** The Universal Voice Runtime thesis was architecture-validated but
  provider-validated only for OmniVoice. Fish Audio real inference was blocked (codec/VRAM).
- **Result:** The Cloud readiness gate is now open. The multi-provider thesis is no longer
  architecture-only — Kokoro proves the runtime works with a real non-OmniVoice provider.
- **Related ADRs:** ADR-0008, ADR-0010, ADR-0011; reserved ADR-0012 (provisioning policies),
  ADR-0013 (model categories).
- **See:** `VALIDATION/PROVIDER_VALIDATIONS/kokoro-validation-report.md`

## Decision 2 — Variant provisioning policies per Creation Source (reserved ADR-0012)

- **Status:** OPEN.
- **Context:** ADR-0010's "rebuild every variant from the Source Asset" applies only to
  `SOURCE_ASSET` voices. Other origins (`PRESET_VOICE`, etc.) need their own strategy.
- **Impact:** Provisioning pipeline correctness across origin types.
- **Related ADRs:** ADR-0010, ADR-0011.

## Decision 3 — Model categories (reserved ADR-0013)

- **Status:** OPEN.
- **Context:** Classifying providers — cloning vs preset vs training — to drive provisioning
  and capability expectations.
- **Related ADRs:** ADR-0011.

## Decision 4 — Auth vendor seam (Clerk)

- **Status:** OPEN (Phase 4, Cloud).
- **Context:** First `AuthProvider` adapter choice and principal-resolution wiring.
- **Impact:** Cloud multi-tenancy.

## Decision 5 — Payments/payouts vendor seam (Stripe + Connect)

- **Status:** OPEN (Phases 5–6, Cloud).
- **Context:** First `BillingProvider`/`PaymentProvider`/`PayoutProvider` adapters.

## Decision 6 — SQLite→Postgres cut-over and Alembic adoption

- **Status:** OPEN (Phase 8, Cloud).
- **Context:** Alembic is adopted only at the Cloud Postgres cut-over; CE stays on the
  idempotent SQLite runner.
- **Related:** `../architecture/08-MIGRATION_ARCHITECTURE.md`.

## Decision 7 — pgvector reconsideration

- **Status:** OPEN, current verdict NO.
- **Context:** Only if semantic voice-similarity becomes a product feature; would need its own
  ADR. Today search runs on derived `characteristics`.
- **Related:** `../architecture/03-DATA_ARCHITECTURE.md` §6.

## Decision 8 — Marketplace search backend

- **Status:** OPEN (Phase 7, Cloud).
- **Context:** Postgres FTS vs external index for marketplace discovery at scale.

## Decision 9 — Runtime-Service architecture adopted (ADR-0016)

- **Status:** ✅ **RESOLVED** (2026-06-07).
- **Decision:** PeakVox adopts the Runtime-Service architecture as defined by
  [ADR-0016](DECISIONS/adr-0016-models-as-runtime-services.md). PeakVox installs
  *runtimes*, not models. One Model → many Runtimes (CUDA / CPU / local / cloud).
  Migration is sequenced across 7 phases; Phase 1 (ADR + design) is complete with
  no code. Existing in-process model execution continues unchanged.
- **Context:** The Universal Voice Runtime thesis implied a distributed future (see
  `ARCHITECTURE/runtime-architecture.md` §9.2) but never made the substrate a
  first-class seam. ADR-0016 closes that gap and applies the model-agnostic
  runtime pattern to every edition (Article V §14).
- **Result:** The next workstream is **Phase 2** of the Runtime-Service migration
  (Runtime Manager skeleton + `DockerRuntimeDriver`). This preempts Cloud
  architecture planning; the same target is shared by CE and Cloud, so investing
  in Phase 2 unblocks both.
- **Related:** ADR-0016; [`SPECS/FEATURES/models-as-runtime-services/`](SPECS/FEATURES/models-as-runtime-services/);
  Architecture §9.2 (distributed execution, now formalized).
- **See:** `VALIDATION/PROVIDER_VALIDATIONS/` (Phase 3 will add
  `kokoro-runtime-validation-report.md`).

## Decision 10 — Runtime-Service Phase 2 implementation ADR

- **Status:** ✅ **RESOLVED** (2026-06-07).
- **Decision:** [ADR-0017 — Runtime Services Implementation](DECISIONS/adr-0017-runtime-services-implementation.md)
  is **Accepted** (2026-06-07). The five open questions are
  resolved as **accepted architecture** by reference to ADR-0017.
  Phase 2 implementation may begin safely.
- **Resolution (per ADR-0017):**
  1. **Runtime endpoint discovery** — `RuntimeManager.resolve` is
     the single resolution point (ADR-0017 §3.4).
  2. **Runtime upgrade / rollback** — versioned images; pin by
     `spec.image.digest`; declarative rollback via descriptor change
     (ADR-0017 §1.4, §4.3).
  3. **GPU allocation protocol** — Runtime Service owns the device;
     `RuntimeManager` only observes capability and reports health
     (ADR-0017 §4.4, §5.2).
  4. **Runtime health contract** — separate liveness (`/health`) and
     readiness (`/ready`); readiness = can serve inference;
     `RuntimeManager` refuses to route to not-ready instances
     (ADR-0017 §6.1, §6.2).
  5. **Backend-to-runtime authentication** — CE default = `none`;
     Cloud deferred to the Cloud ADR; `HTTPTransport` accepts an
     optional bearer token (ADR-0017 §9, §10).
- **Result:** Phase 2 implementation may begin. Sub-phase 2A
  (Foundations: `RuntimeDescriptor`, `RuntimeRegistry`,
  `RuntimeManager`, `RuntimeDriver` protocol, `RuntimeInstance`,
  `RuntimeEventBus`) is the next P0 work item.
- **Related:** [ADR-0017](DECISIONS/adr-0017-runtime-services-implementation.md);
  [ADR-0016](DECISIONS/adr-0016-models-as-runtime-services.md);
  [`SPECS/FEATURES/runtime-services-implementation/`](SPECS/FEATURES/runtime-services-implementation/);
  [`SPECS/FEATURES/models-as-runtime-services/TASKS.md` §2](SPECS/FEATURES/models-as-runtime-services/TASKS.md).

> The historical "Implementation direction (non-binding, seed for
> ADR-0017)" notes that previously lived here have been **resolved**
> into the canonical architecture of ADR-0017. They are no longer
> needed as decision seeds.

## Decision 11 — Future runtime drivers (Kubernetes, Podman, LocalProcess)

- **Status:** OPEN (no ADR written).
- **Context:** ADR-0016 names `DockerRuntimeDriver` (CE, first), and lists
  `KubernetesRuntimeDriver` (Cloud), `PodmanRuntimeDriver`, and
  `LocalProcessDriver` as future implementations. None is implemented. They
  exist in the ADR to validate the abstraction.
- **Impact:** Each driver becomes its own ADR when its edition begins
  (Cloud → `KubernetesRuntimeDriver`; alternative deployments → Podman;
  dev/single-process testing → LocalProcess). The shared interface is locked
  by ADR-0016; per-driver ADRs cover substrate-specific semantics only.
- **Related:** ADR-0016 §"Future drivers".

## Decision 12 — Runtime Persistence (future ADR)

- **Status:** OPEN (no ADR written; non-blocking for ADR-0017 accept).
- **Context:** ADR-0017 deliberately keeps the `RuntimeManager` cache
  in-memory only. After a backend restart, the cache is empty and
  runtimes must be re-activated. This is appropriate for Phase 2.
  Future requirements will likely require persistence:
  - **Multiple runtime deployments** — fleet management.
  - **Operational dashboards** — runtime status, history, capacity.
  - **Historical health tracking** — `/ready` transitions, restart
    counts, error rates.
  - **Cloud orchestration** — multi-region, multi-tenant runtime
    state.
  - **Runtime metrics and observability** — counters, time series.

  Possible persistence surfaces (all **infrastructure state**, not
  domain state; forbidden patterns `RuntimeServiceEntity`,
  `RuntimeServiceRepository`, `RuntimeVariant`, `RuntimeArtifact`
  from ADR-0016 still apply):

  - `runtime_instances` — last-known state of each instance (id,
    state, endpoint, image identity, started_at, last_health_at,
    health_state). Infrastructure bookkeeping owned by the
    `RuntimeManager`.
  - `runtime_events` — append-only log of `runtime.<op>.*` events
    emitted by the `RuntimeEventBus`. Used for audits and
    dashboards.
  - `runtime_installations` — record of which runtime version is
    currently installed on which host / cluster (Cloud-relevant).
  - **API surface** — `GET /api/v1/runtimes`,
    `GET /api/v1/runtimes/{id}`,
    `GET /api/v1/runtimes/{id}/events` (read-only; not in
    ADR-0017's scope).

- **Impact:** Future ADR. **Not blocking for ADR-0017 acceptance.**
  ADR-0017 explicitly defers persistence to this future work
  (`DESIGN §3.5`: "The manager does **not** persist operational
  state").
- **Constraints:** Per Constitution §18, any new tables follow
  the SQLite-safe runner in `app/core/migrations.py`; migrations
  are additive and idempotent. Per ADR-0016, the domain
  boundary is preserved: persistence tables are infrastructure
  state, not domain entities.
- **Related:** ADR-0017 §3.5 (in-memory cache, persistence
  deferred); ADR-0016 (domain boundary, forbidden patterns).

---

**Related:** [`DECISIONS/ADR_INDEX.md`](DECISIONS/ADR_INDEX.md) · [`ROADMAP/ROADMAP.md`](ROADMAP/ROADMAP.md) ·
[`DECISIONS/adr-0017-runtime-services-implementation.md`](DECISIONS/adr-0017-runtime-services-implementation.md) ·
[`SPECS/FEATURES/runtime-services-implementation/`](SPECS/FEATURES/runtime-services-implementation/)
