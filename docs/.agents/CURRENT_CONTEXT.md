# CURRENT CONTEXT

> Operational memory. Changes frequently — update at the start and end of every working
> session. Keep it short and current; move history to the execution ledger.

**As of:** 2026-06-05

- **Current focus:** CE hardening after the Phase 3 spine — Voice Library 2.0, variant
  backfill UX, and Fish Audio provider wiring.
- **Current branch:** `feat/peakvox-phase-1`
- **Current execution target:** Stabilize and verify the uncommitted working-tree changes
  (Fish adapter expansion, `schemas/variant.py`, `core/migrations.py`, `models/db.py`,
  `api/generation.py`, related tests), then commit.
- **Current ADR in play:** ADR-0011 (Voice Creation Sources) and ADR-0008/0009 (build
  lifecycle + artifacts) — the surfaces touched by backfill/variant work.
- **Current spec:** `../superpowers/specs/2026-06-04-voice-library-2-design.md`
  and `../superpowers/plans/2026-06-04-variant-backfill-ux.md`.
- **Current blockers:** Fish Audio real inference deferred (codec/VRAM); no GPU in CI.
- **Current validation goal:** prove one non-OmniVoice provider end-to-end through the
  Runtime — this is the gate before any Cloud work.

## Working-tree state (uncommitted)

Modified (per `git status` at session start): `backend/app/api/generation.py`,
`core/config.py`, `core/migrations.py`, `models/db.py`, `schemas/job.py`,
`services/model_adapter.py`, `model_adapters/fish_adapter.py`,
`model_adapters/omnivoice_adapter.py`, `model_catalog.py`, `runtime.py`,
`voice_onboarding.py`, and four test files; `docs/architecture/12-PROVIDER-VALIDATION.md`.
Untracked: `schemas/variant.py`, `tests/test_variants_api.py`,
`docs/fish-audio-blocker-report.md`, and recent plans/specs under `docs/superpowers/`.

**Before further feature work:** run the backend test suite and confirm green; decide
whether the Fish adapter changes are ready to commit.

---

**Related:** [`ACTIVE_WORK.md`](ACTIVE_WORK.md) · [`NEXT_TASK.md`](NEXT_TASK.md) ·
[`HANDOFF.md`](HANDOFF.md) · [`PROJECT_STATE.md`](PROJECT_STATE.md)
