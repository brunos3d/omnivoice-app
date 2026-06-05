# Migrations

CE migrations are **additive + idempotent**, run by the SQLite-safe startup runner —
**not Alembic** (Constitution Art. VI; ADR-aligned with `08-MIGRATION_ARCHITECTURE.md`).

- **Runner / source of truth:** `backend/app/core/migrations.py`
- **Strategy doc:** [`../../ARCHITECTURE/MIGRATION_ARCHITECTURE.md`](../../ARCHITECTURE/migration-architecture.md)
  → canonical [`../../ARCHITECTURE/migration-architecture.md`](../../ARCHITECTURE/migration-architecture.md)

## Rules

1. Add nullable columns / new tables; backfill in code. Never destructive (no drops/renames of
   in-use columns).
2. Every migration must be idempotent (safe to run on every startup).
3. The Voice split preserved `public_voice_id`; consumers were repointed before retiring old
   writes (copy-verify-then-remove).
4. Alembic is introduced **only** at the Cloud Postgres cut-over (Phase 8), baselined to the
   then-current schema.

## Notable migrations (in `migrations.py`)

- Voice / VoiceVariant split + backfill from `voice_profiles` (Phase 3).
- `voice_variant_artifacts` versioning table (ADR-0009).
- Voice source asset / creation source columns (ADR-0010/0011 surfaces).
- Schema-ready commercial tables (Phase 1; empty in CE).

> When adding a migration, record it in [`../EXECUTION_HISTORY/EXECUTION_LEDGER.md`](../EXECUTION_HISTORY/EXECUTION_LEDGER.md)
> and verify it is additive + idempotent.
