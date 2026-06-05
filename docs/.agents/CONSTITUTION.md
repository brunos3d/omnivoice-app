# PeakVox Constitution

> The highest-level invariant layer. These rules are **normative**: every design, ADR,
> spec, and line of code must uphold them. When a proposal conflicts with the constitution,
> the proposal is wrong — or it must first amend the constitution through a superseding ADR.
> Derived from the architecture suite ([`ARCHITECTURE/`](ARCHITECTURE/)) and the ADRs
> ([`DECISIONS/ADR_INDEX.md`](DECISIONS/ADR_INDEX.md), 0001–0011).

Amendment rule: a constitutional article changes **only** by an accepted ADR that explicitly
names the article it revises. Articles are not edited silently.

---

## Article I — Identity of the system

1. **PeakVox is a Universal Voice Runtime, not a model frontend.** The product is the
   Runtime Layer, not any model. (Source: `00-VISION.md`.)
2. **PeakVox is model-agnostic.** No code, schema, API, or UI may be architected around a
   specific model. Adding or removing a model must not change public APIs, Voice IDs, the
   Voice Library, the marketplace, or developer integrations. (ADR-0002, ADR-0004.)
3. **OmniVoice is the first provider, not the center of gravity.** Any provider may be added
   or removed without structural change.

## Article II — The three-concept separation (the spine)

4. **Voice, VoiceVariant, and Model are three separate concepts.** They are related but never
   the same thing. (ADR-0001, ADR-0004.)
   - A **Voice** is a portable, model-agnostic identity and economic asset.
   - A **VoiceVariant** is a model-specific realization (embeddings/checkpoints/refs).
   - A **Model** is an interchangeable inference engine.
5. **`public_voice_id` is a permanent public contract.** It is immutable and survives across
   model providers, edition changes, and variant rebuilds. (ADR-0001, ADR-0004.)
6. **A VoiceVariant is never exposed on the public API.** Variants, embeddings, checkpoints,
   and model-specific artifacts are internal. The public surface speaks only Voice + Model.
   (ADR-0004; `frontend/AGENTS.md`.)
7. **A Voice does not require reference audio.** A voice's origin is a **Creation Source**
   (`SOURCE_ASSET`, `PRESET_VOICE`, and future types), not always a WAV. (ADR-0011.)
   Creation Source (origin) and Variant (realization) are **orthogonal axes**. (ADR-0006,
   ADR-0011.)

## Article III — The Runtime joins the three

8. **The Runtime is the single, model-agnostic generation entry point.** It resolves
   `Voice + Model → VoiceVariant → inference`. All generation routes through
   `PeakVoxRuntime`; nothing bypasses it. (`10-RUNTIME_ARCHITECTURE.md`.)
9. **Nothing above the adapter line imports a model implementation.** Models integrate only
   through the `ModelAdapter` contract. (ADR-0004, `10-RUNTIME_ARCHITECTURE.md`.)
10. **Capabilities are declared, not inferred.** Read `ModelCapabilities`. Never branch on
    model id or model name to detect a feature. (ADR-0003.)

## Article IV — Variants are buildable, versioned, auditable

11. **Variant lifecycle is a defined state machine.** The five-value status machine in
    `variant_lifecycle.py` is authoritative; the Runtime owns `build/rebuild/ensure_variant`.
    (ADR-0008, supersedes ADR-0006 status values.)
12. **Artifacts are versioned, retained, and rollback-able.** Variant realizations are stored
    as versioned `voice_variant_artifacts` rows. (ADR-0009.)
13. **For `SOURCE_ASSET` voices, every variant is reproducible from the Source Asset.** Other
    creation sources use their own provisioning strategy. (ADR-0010, ADR-0011.)

## Article V — Editions and the open-core boundary

14. **CE is the infrastructure layer; Cloud is the ecosystem layer.** Marketplace, creators,
    royalties, credits, payouts, and multi-tenant auth are **Cloud-only**. (ADR-0005,
    `01-PRODUCT_ARCHITECTURE.md`.)
15. **Commercial concepts are schema-ready in CE, never forked.** They exist behind feature
    flags and deployment boundaries from day one, so enabling them in Cloud is wiring, not a
    domain redesign. Commercial tables are empty in CE.
16. **Auth and billing are swappable interfaces.** Clerk and Stripe are the first adapters,
    like the existing identity seam. No vendor is hard-wired into the domain.
17. **Model availability is edition-scoped and licensing-governed.** A model's editions are a
    declared property, not a code branch. (ADR-0005.)

## Article VI — Data and migrations

18. **Migrations are additive and idempotent.** The SQLite-safe runner in
    `app/core/migrations.py` is the CE mechanism — not Alembic. Add nullable columns and
    backfill; never destructive changes. Alembic arrives only at the Cloud Postgres cut-over.
    (`08-MIGRATION_ARCHITECTURE.md`.)
19. **No pgvector** unless a real semantic voice-similarity feature justifies it under its own
    ADR. Voice search/filter runs on derived structured `characteristics`. (Data §6.)
20. **Built-in model metadata is canonical and normalized once.** Provider-backed facts enter
    the registry from canonical sources, then are consumed by API/UI/Runtime. (ADR-0007.)

## Article VII — Truth, evidence, and documentation

21. **Code is proof; documentation is intent.** ADRs are architectural truth about decisions;
    specs are implementation intent; **code is implementation proof.** An ADR being "Accepted"
    is never evidence that the feature is implemented.
22. **Implementation status defines truth.** Claims of "implemented" require code references
    and, ideally, test references. (See `IMPLEMENTATION_STATUS.md`.)
23. **Architecture-validated ≠ provider-validated.** A concept being represented and tested in
    the abstract does not mean a real model runs it end-to-end. Never conflate the two.
24. **Documentation is part of implementation.** A change is not complete until the affected
    documents in `docs/.agents/` (state, status, context, handoff, ledger) are updated.
25. **The knowledge base is navigable without repository search.** Major documents cross-link
    to related docs, ADRs, code, and validations.

## Article VIII — Backward compatibility

26. **The `/api/v1` contract and `public_voice_id` are stable across editions and model
    changes.** Breaking changes require a new version (`/v2`) and a deprecation policy, never a
    silent change. (`04-API_ARCHITECTURE.md`.)

---

**Related:** [`CONTEXT/VISION.md`](CONTEXT/VISION.md) · [`DECISIONS/ADR_INDEX.md`](DECISIONS/ADR_INDEX.md) ·
[`DOMAIN_MODEL.md`](DOMAIN_MODEL.md) · [`AGENT_WORKFLOW.md`](AGENT_WORKFLOW.md)
