# CURRENT CONTEXT

> Operational memory. Changes frequently — update at the start and end of every working
> session. Keep it short and current; move history to the execution ledger.

**As of:** 2026-06-07

- **Current focus:** Phase 2 implementation. ADR-0016 (Accepted) +
  ADR-0017 (Accepted) are the architectural baseline. Architecture
  review passed (0 blocking issues; non-blocking suggestions
  applied: Runtime Persistence added as Decision 12; ADR_INDEX /
  IMPLEMENTATION_STATUS consistency fixed). Sub-phase **2A —
  Foundations** is the next P0 work item. Existing in-process
  model execution continues unchanged.
- **Current branch:** `feat/peakvox-phase-1`
- **Working tree:** clean — this commit accepts ADR-0017,
  resolves `OPEN_DECISIONS.md` Decision 10, adds Decision 12
  (Runtime Persistence — future ADR), and updates state files
  (PROJECT_STATE, NEXT_TASK, CURRENT_CONTEXT, ACTIVE_WORK,
  ROADMAP/*, ADR_INDEX, IMPLEMENTATION_STATUS, OPEN_DECISIONS).
  No code, no migrations, no `runtime-registry/` directory, no
  `RuntimeManager` / `RuntimeDriver` / `RuntimeDescriptor` class,
  no `HTTPTransport`, no `KokoroAdapter` modification, no new
  API endpoints, no Docker integration, no Kokoro migration code.
- **Current ADRs in play:** ADR-0008/0009/0010/0011/0012
  (variant lifecycle, artifacts, source assets, creation
  sources, catalog resources) — the surface touched by the
  Runtime-Service architecture. ADR-0016 and ADR-0017 preserve
  all five. ADR-0017 is the implementation architecture.
- **Current specs:**
  `docs/.agents/SPECS/FEATURES/models-as-runtime-services/`
  (ADR-0016) and
  `docs/.agents/SPECS/FEATURES/runtime-services-implementation/`
  (ADR-0017), plus existing specs.
- **Current blockers:** Fish Audio real inference deferred
  (codec/VRAM); no GPU in CI. These predate ADR-0016 and are
  unaffected.
- **Current validation goal:** Sub-phase 2A is implementation
  (architecture + unit tests). Sub-phase 2C is the first
  provider-validated runtime-service migration (Kokoro + runtime
  service E2E).

---

**Related:** [`ACTIVE_WORK.md`](ACTIVE_WORK.md) · [`NEXT_TASK.md`](NEXT_TASK.md) ·
[`HANDOFF.md`](HANDOFF.md) · [`PROJECT_STATE.md`](PROJECT_STATE.md) ·
[`docs/.agents/SPECS/FEATURES/models-as-runtime-services/`](SPECS/FEATURES/models-as-runtime-services/) ·
[`docs/.agents/SPECS/FEATURES/runtime-services-implementation/`](SPECS/FEATURES/runtime-services-implementation/) ·
[`docs/.agents/DECISIONS/adr-0016-models-as-runtime-services.md`](DECISIONS/adr-0016-models-as-runtime-services.md) ·
[`docs/.agents/DECISIONS/adr-0017-runtime-services-implementation.md`](DECISIONS/adr-0017-runtime-services-implementation.md)
