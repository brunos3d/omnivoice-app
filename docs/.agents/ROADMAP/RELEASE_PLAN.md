# Release Plan

> How phases turn into shippable releases. Each phase is ordered to be independently shippable,
> keep CE working, and preserve the `public_voice_id` / `/api/v1` contracts.

**As of:** 2026-06-05

## Release lines

- **CE (Community Edition)** — self-hosted via Docker Compose. The current shippable line.
- **Cloud (PeakVox Cloud)** — managed, multi-tenant. Not yet released; gated behind the
  provider-validation gate.

## CE release readiness

| Capability | Ready to ship in CE? |
|---|---|
| Local model registry + lifecycle (state) | Yes |
| Voice library + Voice/Variant split + variant dashboard | Yes |
| Generation through the Runtime (OmniVoice) | Yes (OmniVoice only) |
| Versioned `/api/v1` | Yes (freeze/SDK pending P9) |
| Multi-provider generation | No — only OmniVoice has a real engine |

**Current CE release blocker for "multi-provider" claims:** provider validation (M2). CE can
ship as a single-real-provider runtime today; it cannot honestly advertise N working providers.

## Cut-over events (future)

- **Postgres + Alembic** adopted only at the Cloud cut-over (Phase 8); CE remains on the
  idempotent SQLite runner.
- **`pv_` API key prefix** transition (old `ov_` accepted) at API harden (Phase 9).

## Branch / merge

- Active development on `feat/peakvox-phase-1`; integrate to `main` via the
  `superpowers:finishing-a-development-branch` flow when phases complete and tests pass.

---

**Related:** [`MILESTONES.md`](MILESTONES.md) · [`ROADMAP.md`](../ARCHIVE/LEGACY/ROADMAP.md) ·
[`../ARCHITECTURE/MIGRATION_ARCHITECTURE.md`](../ARCHITECTURE/migration-architecture.md)
