# CURRENT CONTEXT

> Operational memory. Changes frequently — update at the start and end of every working
> session. Keep it short and current; move history to the execution ledger.

**As of:** 2026-06-08

- **Current focus:** **Runtime-Canonical Models Page** is
  VALIDATED (2026-06-08). **TASK 12 (Runtime Registry
  Expansion)** is VALIDATED. The Runtime Registry now
  hosts three independent runtime implementations
  (`kokoro-82m`, `omnivoice-base`, `f5-tts-base`). The
  Models page renders all three with zero hardcoded
  assumptions. The Kokoro runtime container produces
  real audio (4.45s WAV, 24kHz mono PCM) end-to-end
  through the 5-endpoint Runtime Service Contract.
  Workstream A (Models page) + Workstream B (Runtime
  Registry expansion) are both complete and validated.
  Audit:
  [`SPECS/FEATURES/runtime-canonical-models-page/audits/`](SPECS/FEATURES/runtime-canonical-models-page/audits/).
  Phase 2 (Runtime Services) remains COMPLETE; the
  Phase 3 full-stack convergence is now mid-flight
  with the runtime-canonical Models page + the
  multi-runtime registry expansion as the first two
  deliverables.
- **Current branch:** `feat/peakvox-phase-1`
- **Current ADRs in play:** ADR-0008/0009/0010/0011/0012
  (variant lifecycle, artifacts, source assets, creation
  sources, catalog resources) — the surface touched by the
  Runtime-Service architecture. ADR-0016 and ADR-0017
  preserve all five. ADR-0017 is the implementation
  architecture; both are now Accepted+Implemented.
- **Current specs:**
  `docs/.agents/SPECS/FEATURES/models-as-runtime-services/`
  (ADR-0016) and
  `docs/.agents/SPECS/FEATURES/runtime-services-implementation/`
  (ADR-0017), plus existing specs.
- **Current blockers:** Fish Audio real inference deferred
  (codec/VRAM); no GPU in CI. These predate Phase 2A and
  are unaffected. Phase 3 requires a real
  `peakvox/kokoro-runtime` container in the docker-compose
  CI lane; the E2E scaffold is in place but gated.
- **Current validation goal:** Phase 3 lands the
  E2E-validated Kokoro G6 report (real audio E2E through
  the runtime service in the docker-compose CI lane), G7
  (Performance) and G8 (Error recovery) reports. Phase 3
  makes the runtime-service path the DEFAULT for Kokoro in
  CE; the in-process path is preserved as a fallback.

---

**Related:** [`ACTIVE_WORK.md`](ACTIVE_WORK.md) · [`NEXT_TASK.md`](NEXT_TASK.md) ·
[`HANDOFF.md`](HANDOFF.md) · [`PROJECT_STATE.md`](PROJECT_STATE.md) ·
[`docs/.agents/SPECS/FEATURES/models-as-runtime-services/`](SPECS/FEATURES/models-as-runtime-services/) ·
[`docs/.agents/SPECS/FEATURES/runtime-services-implementation/`](SPECS/FEATURES/runtime-services-implementation/) ·
[`docs/.agents/DECISIONS/adr-0016-models-as-runtime-services.md`](DECISIONS/adr-0016-models-as-runtime-services.md) ·
[`docs/.agents/DECISIONS/adr-0017-runtime-services-implementation.md`](DECISIONS/adr-0017-runtime-services-implementation.md)
