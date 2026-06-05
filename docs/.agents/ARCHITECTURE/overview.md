# PeakVox Architecture — Overview

**Status:** Phase 0 — architectural plan. No implementation in this cycle.
**Audience:** maintainers and contributors planning the evolution of this codebase from a
single-model OmniVoice frontend into **PeakVox**, a model-agnostic voice infrastructure
platform.

> This is the index for the PeakVox architecture suite. Each linked document owns one
> concern. Decisions that are expensive to reverse are captured as ADRs under
> [`adrs/`](../DECISIONS).
>
> **Read [00 — Vision](../CONTEXT/VISION.md) first** — it is the north star every document and future
> decision must stay aligned with. PeakVox is a **Universal Voice Runtime**, not a model
> frontend.

---

## 1. What PeakVox is

PeakVox is a **voice infrastructure and ecosystem platform** for speech generation. It is
to speech what a combination of OpenRouter (model-agnostic routing), Hugging Face (model +
asset registry), LM Studio (local self-hosted runtime), and ElevenLabs (voice products +
creator economy) is to text and audio more broadly — but focused exclusively on **voice**.

The platform is **model-agnostic**. OmniVoice is no longer *the product*; it is **the first
of many model providers** (OmniVoice Base, OmniVoice Singing, Fish Audio, Kokoro, OpenVoice,
and future open models). The product is the platform that sits above all of them.

## 2. The one decision everything hangs off

PeakVox treats three concepts as **completely separate** (today they are fused inside
`VoiceProfile`). They are related but never the same thing — see
[ADR-0004](../DECISIONS/adr-0004-voice-variant-model-separation.md) for the binding rule:

```
MODEL ............ an inference engine            (a way to synthesise speech)
VOICE ............ a model-agnostic identity      (a reusable, ownable economic asset)
VOICE_VARIANT .... a model-specific realization   (the artifacts one model needs for a voice)
```

The **stable public contract** is:

```
Voice  +  Model  ──▶  VoiceVariant  ──▶  generated speech
```

A caller references a **Voice** and a **Model**; the platform resolves the correct
**VoiceVariant** (building it through the variant build lifecycle if it does not yet exist —
see [ADR-0008](../DECISIONS/adr-0008-voice-variant-build-lifecycle.md)). The contract stays stable even
when the underlying model changes. This split is the foundation for multi-model support, the
marketplace, the creator economy, royalties, and cloud scale. The component that joins the
three at request time — resolving `Voice + Model → VoiceVariant → inference` — is the
[Runtime](runtime-architecture.md). See [ADR-0001](../DECISIONS/adr-0001-voice-variant-split.md),
[ADR-0004](../DECISIONS/adr-0004-voice-variant-model-separation.md), and
[Domain Architecture](domain-architecture.md). Built-in model metadata is governed by
[ADR-0007](../DECISIONS/adr-0007-canonical-model-metadata.md): provider-backed facts are normalized once
into the registry and then consumed by the API/UI/Runtime. Variant lifecycle and build
orchestration is governed by [ADR-0008](../DECISIONS/adr-0008-voice-variant-build-lifecycle.md);
artifact versioning, retention, and rollback are governed by
[ADR-0009](../DECISIONS/adr-0009-artifact-versioning-and-retention.md).

## 3. Editions: infrastructure vs ecosystem

| | **Community Edition (CE)** | **PeakVox Cloud** |
|---|---|---|
| Role | **Infrastructure layer** | **Ecosystem layer** |
| Hosting | Self-hosted (Docker Compose) | Managed, multi-tenant |
| Core generation | ✅ TTS, cloning, design, singing | ✅ |
| Model management | ✅ install / activate / run local models | ✅ |
| API usage | ✅ local keys | ✅ metered, per-account keys |
| Auth | None (local owner) | Clerk-backed accounts + roles |
| Marketplace / creators | **Schema-ready, disabled** | ✅ |
| Credits / billing / payouts / royalties | **Schema-ready, disabled** | ✅ |

**Open-core boundary:** the marketplace, creator economy, royalties, credits, transactions,
payouts, and multi-tenant auth are **Cloud-only**. Their **domain models, database entities,
and API boundaries are present in CE from day one**, disabled behind feature flags and
deployment boundaries, so adding them in Cloud is wiring — never a domain redesign. CE is
genuinely useful on its own; Cloud adds the ecosystem. See
[Product Architecture](product-architecture.md) and the existing
[COMMERCIAL_MODEL](../ARCHIVE/LEGACY/COMMERCIAL_MODEL.md).

## 4. Document map

| Doc | Owns |
|---|---|
| [00 — Vision](../CONTEXT/VISION.md) | **North star.** PeakVox as a Universal Voice Runtime; the binding principles all decisions follow |
| [01 — Product Architecture](product-architecture.md) | Editions, personas, capability matrix, feature flags, deployment boundaries |
| [02 — Domain Architecture](domain-architecture.md) | Bounded contexts; Model / Voice / VoiceVariant / Creator / Credits / Marketplace |
| [03 — Data Architecture](data-architecture.md) | Entities, schema-ready tables, SQLite→Postgres, pgvector verdict |
| [04 — API Architecture](api-architecture.md) | `/v1` contract, `/v1/speech/generate`, key namespacing, stability guarantees |
| [05 — Marketplace Architecture](marketplace-architecture.md) | Listings, discovery, preview, royalty-on-use, creator catalog |
| [06 — Cloud Architecture](cloud-architecture.md) | Multi-tenancy, inference workers, storage, deployment topology, observability |
| [07 — Monetization Architecture](monetization-architecture.md) | Credits ledger, revenue split, Stripe Connect payouts, royalty accounting |
| [08 — Migration Architecture](migration-architecture.md) | Rename, VoiceProfile→Voice+Variant split, edition flags, vendor seams, DB migration |
| [09 — Roadmap](../ROADMAP/ROADMAP.md) | The 10 implementation phases, each with goals / DB / backend / frontend / API / risks / migration / order |
| [10 — Runtime Architecture](runtime-architecture.md) | **The core differentiator.** The Universal Voice Runtime: resolution, routing, adapters, GPU/VRAM, lifecycle, local + distributed execution, model classification |
| [11 — Phase 1 Retrospective](../VALIDATION/RETROSPECTIVES/phase-1-retrospective.md) | Honest accounting of what is **architecture-validated** vs **provider-validated**; the validation matrix and the readiness gate before SaaS work |
| [12 — Provider Validation](../VALIDATION/PROVIDER_VALIDATIONS/provider-validation.md) | The 8-gate process a provider must pass to be "supported"; scorecards for OmniVoice/Fish, Kokoro research, registry audit, Models-page + auto-routing analysis |
| [adrs/](../DECISIONS) | Architecture Decision Records: [0001](../DECISIONS/adr-0001-voice-variant-split.md) Voice/Variant split · [0002](../DECISIONS/adr-0002-model-as-first-class-entity.md) Model first-class · [0003](../DECISIONS/adr-0003-model-capability-contract.md) Capability contract · [0004](../DECISIONS/adr-0004-voice-variant-model-separation.md) Voice/Variant/Model separation · [0007](../DECISIONS/adr-0007-canonical-model-metadata.md) canonical model metadata · [0008](../DECISIONS/adr-0008-voice-variant-build-lifecycle.md) variant build lifecycle · [0009](../DECISIONS/adr-0009-artifact-versioning-and-retention.md) artifact versioning · [0010](../DECISIONS/adr-0010-voice-source-assets-and-automatic-variant-provisioning.md) voice source assets + automatic variant provisioning · [0011](../DECISIONS/adr-0011-voice-creation-sources.md) voice creation sources |

## 5. Relationship to existing docs

This suite **supersedes and generalises** the single-model framing of the older docs while
preserving their decisions:

- [`SAAS_ARCHITECTURE.md`](../ARCHIVE/LEGACY/SAAS_ARCHITECTURE.md) — the SaaS-ready seams (identity,
  rate-limit, owner_id, `public_voice_id`, edition flag) are the substrate PeakVox builds on.
- [`VOICE_MODEL.md`](../ARCHIVE/LEGACY/VOICE_MODEL.md) — the Voice identity concept; PeakVox splits its
  model-specific fields into `VoiceVariant`.
- [`COMMERCIAL_MODEL.md`](../ARCHIVE/LEGACY/COMMERCIAL_MODEL.md) / [`ROADMAP.md`](../ARCHIVE/LEGACY/ROADMAP.md) — the
  open-core strategy, now extended with the creator/marketplace ecosystem.

## 6. What already exists (the head start)

PeakVox is **not greenfield**. Already shipped on `main`:

- A **persisted model registry** (`models` table, `model_registry`, `model_catalog`,
  `model_providers/` plugin base, `/models` API) — Model is already a first-class entity.
- A **voice identity foundation** (`public_voice_id`, derived `characteristics`,
  `voice_repository`, `owner_id` everywhere).
- An **API platform** (hashed keys, versioned `/api/v1`, identity + rate-limit seams).
- **Edition awareness** (`settings.EDITION`, `editions` column on `Model`).

The plan reframes and extends this foundation rather than replacing it. See the
[Roadmap](../ROADMAP/ROADMAP.md) for what is "already done → harden" vs genuinely new.
