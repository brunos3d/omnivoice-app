# CURRENT CONTEXT

> Operational memory. Changes frequently — update at the start and end of every working
> session. Keep it short and current; move history to the execution ledger.

**As of:** 2026-06-07

- **Current focus:** Phase 2 implementation. ADR-0016 (Accepted) +
  ADR-0017 (Accepted) are the architectural baseline. **Sub-phase
  2A is COMPLETE (2026-06-07):** 9 new modules + 9 test files
  delivered; 76 new tests, 0 regressions, 401 pre-existing
  tests pass. The next sub-phase is **2B (DockerRuntimeDriver)**.
- **Current branch:** `feat/peakvox-phase-1`
- **Working tree:** clean — this commit lands the Phase 2A
  implementation: 5 new modules in `backend/app/services/` and
  4 modified/new test files (76 new tests, 401/401 pre-existing
  tests pass). Plus state file updates (IMPLEMENTATION_STATUS,
  NEXT_TASK, CURRENT_CONTEXT, ACTIVE_WORK, PROJECT_STATE,
  ROADMAP/*).
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
  (codec/VRAM); no GPU in CI. These predate Phase 2A and are
  unaffected.
- **Current validation goal:** Sub-phase 2A is implementation
  (architecture + unit tests). Sub-phase 2B introduces the
  first concrete driver (mocked in tests). Sub-phase 2C is the
  first provider-validated runtime-service migration (Kokoro +
  runtime service E2E).

---

**Related:** [`ACTIVE_WORK.md`](ACTIVE_WORK.md) · [`NEXT_TASK.md`](NEXT_TASK.md) ·
[`HANDOFF.md`](HANDOFF.md) · [`PROJECT_STATE.md`](PROJECT_STATE.md) ·
[`docs/.agents/SPECS/FEATURES/models-as-runtime-services/`](SPECS/FEATURES/models-as-runtime-services/) ·
[`docs/.agents/SPECS/FEATURES/runtime-services-implementation/`](SPECS/FEATURES/runtime-services-implementation/) ·
[`docs/.agents/DECISIONS/adr-0016-models-as-runtime-services.md`](DECISIONS/adr-0016-models-as-runtime-services.md) ·
[`docs/.agents/DECISIONS/adr-0017-runtime-services-implementation.md`](DECISIONS/adr-0017-runtime-services-implementation.md)
