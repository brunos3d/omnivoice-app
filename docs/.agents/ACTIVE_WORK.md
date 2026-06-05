# ACTIVE WORK

> Only work that is **actively being executed right now**. No roadmap, no future ideas, no
> speculative work — those live in [`ROADMAP/BACKLOG.md`](ROADMAP/BACKLOG.md) and
> [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md). When an item is no longer being worked, move it
> to the execution ledger or remove it.

**As of:** 2026-06-05 · **Branch:** `feat/peakvox-phase-1`

## In flight

1. **Fish Audio adapter expansion + variant schema.** Uncommitted changes to
   `services/model_adapters/fish_adapter.py`, `services/model_adapter.py`,
   `schemas/variant.py` (new), `core/migrations.py`, `models/db.py`,
   `api/generation.py`, and tests (`test_fish_adapter.py`, `test_variants_api.py`,
   `test_adapter_realization_surface.py`, `test_universal_voice_asset.py`,
   `test_runtime_variant_lifecycle.py`).
   - **State:** code present, not committed; tests must be confirmed green this session.
   - **Provider validation:** still blocked (see provider blocker report). Architecture-level
     only.

2. **Provider validation documentation.** `docs/architecture/12-PROVIDER-VALIDATION.md`
   modified; `docs/fish-audio-blocker-report.md` added (untracked).

## Not in flight (explicitly paused)

- Cloud phases (auth/billing/creators/marketplace) — held behind the provider-validation
  readiness gate. Do not start.

---

**Related:** [`NEXT_TASK.md`](NEXT_TASK.md) · [`CURRENT_CONTEXT.md`](CURRENT_CONTEXT.md) ·
[`IMPLEMENTATION/EXECUTION_HISTORY/EXECUTION_LEDGER.md`](IMPLEMENTATION/EXECUTION_HISTORY/EXECUTION_LEDGER.md)
