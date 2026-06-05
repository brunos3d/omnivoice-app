# PeakVox — Implementation Roadmap

**Owns:** the phased execution plan. Ten phases, each with **goals · database · backend ·
frontend · API · risks · migration strategy · execution order**. Phases are ordered so each is
independently shippable, keeps CE working, and preserves the `public_voice_id` / `/api/v1`
contracts.

> This roadmap is the bridge from architecture to implementation tasks. Tasks are generated
> **per phase**, after this plan is approved. Legend: 🟩 largely exists → harden · 🟨 partial ·
> 🟥 new.
>
> The **Runtime Layer** is cross-cutting, not a single phase — its concerns map across Phases 2
> (adapter + capability contract), 3 (variant resolution), 8 (distributed workers / VRAM
> scheduling), and 10 (autoscaling). See the mapping in
> [Runtime §10](../ARCHITECTURE/runtime-architecture.md).

| # | Phase | State |
|---|---|---|
| 1 | Platform Foundations | 🟨 |
| 2 | Model Registry | 🟩 |
| 3 | Voice Architecture (Voice/Variant split) | 🟥 **core** |
| 4 | Authentication | 🟥 (Cloud) |
| 5 | Billing | 🟥 (Cloud) |
| 6 | Creator System | 🟥 (Cloud) |
| 7 | Marketplace | 🟥 (Cloud) |
| 8 | Cloud Infrastructure | 🟨 (Cloud) |
| 9 | Public API | 🟩 → harden |
| 10 | Production Scaling | 🟥 (Cloud) |

---

## Phase 1 — Platform Foundations 🟨

**Goals:** establish PeakVox framing — feature flags, schema-ready commercial tables, the
vendor seams (as interfaces with Null/Local adapters), and the rename groundwork — so every
later phase is wiring, not redesign.

- **Database:** create the schema-ready commercial tables (`creators`, `marketplace_listings`,
  `credit_ledgers`, `transactions`, `royalties`, `payouts`, `roles`) — empty, additive.
- **Backend:** `settings.features` from `settings.EDITION`; define `AuthProvider`,
  `BillingProvider`, `PaymentProvider`, `PayoutProvider` interfaces + Null/Local adapters;
  edition-gated router mounting; `app/cloud/…` module boundary.
- **Frontend:** PeakVox branding; nav gated by feature flags (commercial nav hidden in CE).
- **API:** none breaking; key prefix accepts `pv_`/`ov_`.
- **Risks:** scope creep into building features now (mitigate: tables + seams only, no logic).
- **Migration:** additive idempotent migration; flags off in CE. No data change.
- **Order:** flags → seam interfaces → schema-ready tables → branding/nav.

## Phase 2 — Model Registry 🟩 (harden + extend)

**Goals:** make Model a fully first-class, versioned, lifecycle-managed entity with provider
+ licensing metadata and Hugging Face install support.

- **Database:** add `models.requirements`, `license`, `provider_metadata`, `deprecated_at`;
  establish the version-row rule (consider `model_versions` if needed).
- **Backend:** model lifecycle (`discover/install/activate/deactivate/update/deprecate`); HF
  integration (manifest fetch, weights download into the model cache); the **Model Capability
  Contract** (the frozen, versioned capability superset + `get_capabilities()` on the adapter,
  [ADR-0003](../DECISIONS/adr-0003-model-capability-contract.md)); harden the `ModelAdapter` contract
  ([Runtime §6](../ARCHITECTURE/runtime-architecture.md); provider base already exists).
- **Frontend:** model manager UI (install from HF, activate/deactivate, version, capabilities,
  requirements); already-present ModelSelector reads richer metadata.
- **API:** extend `GET /v1/models` with capabilities/requirements/license; admin lifecycle
  endpoints (Cloud-gated for write).
- **Risks:** untrusted model code/weights (mitigate: provider sandboxing, signed manifests,
  admin-only install in Cloud); large downloads (progress + resumable).
- **Migration:** additive columns; built-ins re-seeded with new metadata.
- **Order:** metadata columns → lifecycle service → HF install → UI.

## Phase 3 — Voice Architecture (Voice / VoiceVariant split) 🟥 **core**

**Goals:** the central refactor — split identity from realization; stand up the onboarding
pipeline and variant resolution. Everything downstream depends on this.

- **Database:** create `voices` + `voice_variants`; backfill from `voice_profiles` (OmniVoice
  variant); add `generation_jobs.voice_id` + `voice_variant_id`. (Migration §2.)
- **Backend:** `voice_repository` → reads/writes `voices`; new `voice_variant_repository`;
  onboarding pipeline (validate → process → create Voice → build variant); `Voice+Model→Variant`
  resolution in generation; lazy/stale variant rebuild.
- **Frontend:** voice library + creation read identity from `voices`; variant status surfaced
  where relevant; generation references `voice` + `model`.
- **API:** `/v1/voices` returns identity (`public_voice_id`); `/v1/speech/generate` resolves
  variant transparently (no client change).
- **Risks:** data-integrity during split (mitigate: keep `voice_profiles` read-only fallback;
  verify backfill counts); storage path moves (copy-verify-then-remove).
- **Migration:** the central additive migration; `public_voice_id` preserved; consumers
  repointed before retiring old table.
- **Order:** tables + backfill → repositories → resolution in generation → repoint API/UI →
  onboarding pipeline → retire old writes.

## Phase 4 — Authentication 🟥 (Cloud)

**Goals:** real accounts, roles, and multi-tenant principal resolution in Cloud — CE stays
local-owner.

- **Database:** `roles`/`user_roles`; map Clerk identities → `users`.
- **Backend:** `ClerkAuthProvider` adapter implementing `AuthProvider`; principal resolution as
  a FastAPI dependency on every router; repository queries filter by resolved `owner_id`; role
  checks (`user`/`creator`/`admin`).
- **Frontend:** Clerk sign-in/up in Studio; role-gated UI; CE shows no auth.
- **API:** keys resolve to account + plan; sessions for Studio; wire format unchanged.
- **Risks:** tenancy leaks (mitigate: enforce owner filter centrally + tests that assert
  cross-tenant denial); vendor lock-in (mitigate: the adapter seam).
- **Migration:** additive; CE unaffected (`LocalOwnerAuthProvider`).
- **Order:** auth interface (done P1) → Clerk adapter → principal dependency → owner-filter
  enforcement → roles.

## Phase 5 — Billing 🟥 (Cloud)

**Goals:** credits, metering, and the consume/reserve flow — money in, generation gated.

- **Database:** activate `credit_ledgers` + `transactions` (append-only, immutable in PG).
- **Backend:** `StripeBillingAdapter`/`StripeAdapter`; metering store fed by
  `generation.completed`; credit reserve→settle→release around inference; quota checks.
- **Frontend:** plans, credit balance, top-ups, usage dashboard.
- **API:** `402` on exhaustion; usage in job responses; `/billing` (Cloud) endpoints.
- **Risks:** double-spend/race on balance (mitigate: ledger as source of truth + reserve
  semantics + reconciliation); webhook reliability (idempotent handlers).
- **Migration:** activate tables (created in P1); Null→Stripe adapter swap in Cloud.
- **Order:** ledger + transactions → metering → reserve/settle → Stripe billing → UI.

## Phase 6 — Creator System 🟥 (Cloud)

**Goals:** creators as owners of voices and recipients of royalties.

- **Database:** activate `creators`; `voices.creator_id` populated; `royalty_config`.
- **Backend:** creator profiles, verification flow, Stripe Connect onboarding
  (`PayoutProvider`), royalty config; royalty accrual on marketplace generations.
- **Frontend:** Creator Console (profile, voices, analytics, royalties, payouts).
- **API:** `/creator/*` (Cloud); voices expose creator attribution.
- **Risks:** ownership/consent disputes (mitigate: verification + provenance via
  `public_voice_id` + usage policy); payout compliance (delegate KYC/tax to Connect).
- **Migration:** activate `creators`; backfill existing voices to a default creator on
  Cloud import.
- **Order:** creator profile + verification → Connect onboarding → royalty config → accrual →
  console.

## Phase 7 — Marketplace 🟥 (Cloud)

**Goals:** publish, discover, preview, use — with royalty-on-use closing the economic loop.

- **Database:** activate `marketplace_listings`; `royalties` rows on use.
- **Backend:** publish flow (gates on verified creator + ready variant + preview); discovery
  over `characteristics` + text search (**no pgvector**); royalty-on-use via
  `generation.completed`; moderation/takedown.
- **Frontend:** Marketplace (browse/search/filter/preview/use); publish UI in Creator Console.
- **API:** `/v1/marketplace/*` (browse/preview); `generate` accepts any public `voice`.
- **Risks:** abuse/IP misuse (mitigate: moderation queue, takedown = unlist + freeze accruals);
  search relevance at scale (mitigate: FTS/external index, facets).
- **Migration:** activate listings; flip `is_public` semantics via publish flow.
- **Order:** listing model → publish flow → discovery → preview/use → royalty loop →
  moderation.

## Phase 8 — Cloud Infrastructure 🟨 (Cloud)

**Goals:** the managed runtime — Postgres, worker pool, storage, topology, observability.

- **Database:** **SQLite→Postgres**; adopt **Alembic** (baseline = current schema);
  pooling; ledger immutability triggers.
- **Backend:** inference worker pool behind a queue (job pipeline already async);
  requirement-aware scheduling; signed-URL/CDN delivery; rate limiter (Redis) replacing the
  no-op seam; metering store.
- **Frontend:** none core (ops/admin dashboards).
- **API:** unchanged contract; download-URL/CDN path behind same endpoints.
- **Risks:** migration cut-over (mitigate: baseline import + verify; CE untouched on SQLite);
  GPU cost/scaling (mitigate: per-model pools, autoscale on queue depth — P10).
- **Migration:** Postgres cut-over per [Migration §6](../ARCHITECTURE/migration-architecture.md); Alembic
  adopted only here.
- **Order:** Postgres+Alembic → queue+workers → storage/CDN → rate limit → observability.

## Phase 9 — Public API 🟩 (harden)

**Goals:** lock the stable, SDK-grade public contract across editions and model changes.

- **Database:** none.
- **Backend:** finalize `Voice+Model→Variant` resolution guarantees; `pv_`-prefixed keys
  (old accepted); capability validation; consistent error model (`402/409/410/422`).
- **Frontend:** "Use in API" examples updated to `/v1/speech/generate`.
- **API:** freeze `/v1`; publish OpenAPI; ship the official SDK; deprecation policy.
- **Risks:** breaking changes leaking into `/v1` (mitigate: contract tests + `/v2` discipline).
- **Migration:** none breaking; key prefix transition.
- **Order:** finalize resolution → error model → freeze + OpenAPI → SDK.

## Phase 10 — Production Scaling 🟥 (Cloud)

**Goals:** scale, reliability, and cost control for the ecosystem at load.

- **Database:** read replicas; partition hot tables (`transactions`, `generation_jobs`) if
  needed; reconciliation jobs.
- **Backend:** autoscaling GPU worker pools per model class; caching (variant + model-load +
  preview); multi-region storage/CDN; SLA monitoring + alerting; abuse/rate hardening.
- **Frontend:** status page; admin scaling/observability dashboards.
- **API:** regional routing; tighter quotas/burst policy.
- **Risks:** cost runaway (mitigate: per-model autoscaling caps + credit-gated demand);
  multi-region consistency (mitigate: primary-write + replica-read, region-pinned storage).
- **Migration:** infra/config only; no domain change.
- **Order:** caching → autoscaling → replicas → multi-region → SLA/observability.

---

## Cross-phase execution order (the critical path)

```
P1 Foundations ─► P2 Model Registry ─► P3 Voice/Variant split  ◄── the spine; gates the rest
                                             │
                 ┌───────────────────────────┼───────────────────────────┐
                 ▼                            ▼                           ▼
        P4 Auth (Cloud) ─► P5 Billing ─► P6 Creators ─► P7 Marketplace
                                             │
                                             ▼
                                   P8 Cloud Infra ─► P9 Public API (harden) ─► P10 Scaling
```

- **P1–P3 are the foundation for everything** and are mostly CE-side (infrastructure layer).
- **P4–P7 are the Cloud ecosystem**, each unlocking the next (auth → money → creators →
  market).
- **P9 (Public API harden)** can proceed in parallel once P3 lands; **P8/P10** are the Cloud
  runtime and scale.

## From roadmap to tasks

After approval, each phase is taken into the **writing-plans** skill to produce a detailed,
test-driven implementation plan (its own spec → plan → execution cycle), starting with the
critical path: **P1 → P2 → P3**.
