# Backlog

> Groomed list of future work not yet active. Active work lives in [`../ACTIVE_WORK.md`](../ACTIVE_WORK.md);
> the single next item in [`../NEXT_TASK.md`](../NEXT_TASK.md). Ordered by priority.

**As of:** 2026-06-05

## P0 — Gating

1. **Stabilize + commit the in-flight working tree** (Fish adapter, variant schema, migrations,
   tests). → currently [`../NEXT_TASK.md`](../NEXT_TASK.md).
2. **First foreign-provider validation** — one non-OmniVoice model generates real audio E2E
   through the Runtime. Blocks all Cloud work. See [`../OPEN_DECISIONS.md`](../OPEN_DECISIONS.md)
   Decision 1.

## P1 — CE hardening (can proceed in parallel)

3. **Phase 9 — Public API harden:** freeze `/v1`, consistent error model (402/409/410/422),
   `pv_` key transition, publish OpenAPI, ship SDK, deprecation policy.
4. **OmniVoice end-to-end audio test** (gated/optional CI lane with weights) to move OmniVoice
   from PARTIAL to VALIDATED on the provider axis.
5. **Kokoro adapter + catalog entry** — exercises the preset-voice (non-cloning) path; stress
   test for ADR-0008/0011 provisioning semantics.

## P2 — Provisioning decisions (write the reserved ADRs when decided)

6. ADR-0012 Variant Provisioning Policies (per Creation Source).
7. ADR-0013 Model Categories (cloning vs preset vs training).

## P3 — Cloud ecosystem (blocked on P0.2)

8. Phase 4 Auth (Clerk adapter + principal resolution + roles).
9. Phase 5 Billing (credits ledger + metering + Stripe).
10. Phase 6 Creators (profiles + Connect + royalties).
11. Phase 7 Marketplace (listings + discovery + royalty-on-use).
12. Phase 8 Cloud Infra (Postgres + Alembic + worker pool + CDN + observability).
13. Phase 10 Production Scaling.

---

**Related:** [`ROADMAP.md`](../ARCHIVE/LEGACY/ROADMAP.md) · [`MILESTONES.md`](MILESTONES.md) ·
[`../OPEN_DECISIONS.md`](../OPEN_DECISIONS.md)
