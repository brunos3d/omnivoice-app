# Current Phase

**As of:** 2026-06-05 · **Branch:** `feat/peakvox-phase-1`

## Phase: CE spine complete → provider-validation gate

Phases 1–3 (including sub-phases 3.5–3.11) are **built and tested**. The platform is a
**single-real-provider Universal Voice Runtime with a multi-provider architecture**.

### Done in this phase

- Platform foundations (flags, vendor seams, schema-ready commercial tables).
- Model registry + canonical metadata + capability contract.
- Voice/Variant split, Runtime exclusivity, ModelAdapter contract, build lifecycle, artifact
  versioning, edition scoping.
- Voice Library 2.0 UI, Variant Dashboard, variant backfill UX.

### In progress

- Stabilizing uncommitted Fish-adapter / variant-schema / migration work (see
  [`../ACTIVE_WORK.md`](../ACTIVE_WORK.md)).

### The gate before the next phase

Do **not** start Cloud phases (4–10). The required exit criterion is **one non-OmniVoice
provider generating real audio end-to-end** through the Runtime. Until then, the
multi-provider thesis is architecture-validated but not provider-validated.

### Candidate next phase

Phase 9 (Public API harden) is the only CE-side phase that can proceed in parallel with the
provider-validation effort.

---

**Related:** [`ROADMAP.md`](../ARCHIVE/LEGACY/ROADMAP.md) · [`../NEXT_TASK.md`](../NEXT_TASK.md) ·
[`../VALIDATION/RETROSPECTIVES/`](../VALIDATION/RETROSPECTIVES/)
