# DOMAIN MODEL

> Every core PeakVox concept, explained so it is understandable **without opening the ADRs**.
> The ADRs and architecture docs are the formal sources; this is the readable map. Canonical
> detail: [`ARCHITECTURE/domain-architecture.md`](ARCHITECTURE/domain-architecture.md).

The whole model hangs off one sentence:

```
Voice  +  Model  ──▶  VoiceVariant  (built from a VoiceSourceAsset or other Creation Source)
                                     ──▶  VoiceVariantArtifact (versioned)  ──▶  Generation
```

The **Runtime** is the component that performs the arrow at request time.

---

## Voice

A **Voice** is a portable, model-agnostic **identity** and economic asset. It is what a user,
developer, or creator refers to. Its `public_voice_id` is a **permanent, immutable public
contract** that survives across model providers, edition changes, and variant rebuilds.

A Voice carries identity and derived, structured `characteristics` (used for search/filter) —
**not** model-specific data. A Voice is never "an OmniVoice voice"; it is a PeakVox voice that
*has* an OmniVoice variant. (ADR-0001, ADR-0004.)

## VoiceSourceAsset

The **origin material** for a Voice when the Voice was created from uploaded/recorded audio —
e.g. a reference WAV plus its provenance metadata (filename, content type, size, duration).
For `SOURCE_ASSET` voices, every variant is reproducible from this asset. Not all voices have
one. (ADR-0010.)

## Creation Source

The **origin type** of a Voice — a first-class, model-independent axis. Open taxonomy:
`SOURCE_ASSET` (cloned from reference audio), `PRESET_VOICE` (provider-native preset, no WAV —
e.g. Kokoro), and reserved future types (`MARKETPLACE_VOICE`, `TRAINED_VOICE`,
`IMPORTED_VOICE`, `SYSTEM_VOICE`). Creation Source (where a voice comes from) is **orthogonal**
to VoiceVariant (how a voice is realized per model). (ADR-0011.)

## VoiceVariant

A **VoiceVariant** is a **model-specific realization** of a Voice — the artifacts one model
needs to synthesize that voice (e.g. a reference sample for OmniVoice, a speaker embedding for
Fish, a preset selection for Kokoro). Variants are **replaceable, rebuildable, and never
exposed on the public API**. One Voice has at most one variant per Model. (ADR-0001,
ADR-0004, ADR-0006.)

A variant moves through a **5-state build lifecycle** (owned by the Runtime via
`build/rebuild/ensure_variant`). (ADR-0008, which supersedes ADR-0006's status values.)

## VoiceVariantArtifact

A **versioned** snapshot of a variant's realized artifacts. Artifacts are retained, support
**rollback**, and have CE retention rules. This is what makes a variant auditable and a
rebuild reversible. (ADR-0009.)

## Model

A **Model** is an interchangeable **inference engine** (a provider). It is a first-class,
persisted entity with declared capabilities, canonical metadata, requirements, license, and
edition scoping. Models are added/removed without changing public APIs or Voice IDs.
(ADR-0002, ADR-0005, ADR-0007.)

- **Capabilities are declared, not inferred** (`ModelCapabilities`). UI and Runtime branch on
  declared capabilities, never on model id/name. (ADR-0003.)
- Models integrate through the **`ModelAdapter`** contract; nothing above that line imports a
  model implementation.

## Runtime

The **PeakVoxRuntime** is the single, model-agnostic generation entry point. It:

1. resolves `Voice + Model → VoiceVariant` (building it if missing, via the build lifecycle);
2. validates capabilities/tags and edition availability;
3. orchestrates inference through the model's adapter;
4. manages GPU/VRAM and lifecycle.

All generation routes through it; nothing bypasses it. (`10-RUNTIME_ARCHITECTURE.md`.)

## Generation

A **Generation** is one inference request: `voice + model + text` (+ params) → audio. In CE,
jobs are fire-and-forget: `POST /generate` returns a `job_id`; the client polls
`GET /jobs/{id}`. The wire contract stays stable across model changes.

---

## Cloud / ecosystem concepts (schema-ready in CE, implemented only in Cloud)

These exist as domain models, tables, and API boundaries from day one, disabled behind feature
flags. They are **not implemented** in CE. (ADR-0005; `01-PRODUCT_ARCHITECTURE.md`,
`05`–`07` architecture docs.)

- **Marketplace** — listings, discovery over `characteristics`, preview, royalty-on-use. A
  published Voice is consumable by any account through the same `generate` contract.
- **Creator** — an owner of Voices and recipient of royalties; verification + Stripe Connect
  onboarding.
- **Billing** — credits ledger, metering, reserve→settle→release around inference; Stripe.
- **Cloud** — multi-tenant auth (Clerk), inference worker pool, Postgres + Alembic, storage/CDN,
  observability, autoscaling.

---

**Related:** [`CONSTITUTION.md`](CONSTITUTION.md) ·
[`ARCHITECTURE/domain-architecture.md`](ARCHITECTURE/domain-architecture.md) ·
[`ARCHITECTURE/data-architecture.md`](ARCHITECTURE/data-architecture.md) ·
[`DECISIONS/ADR_INDEX.md`](DECISIONS/ADR_INDEX.md) · [`ARCHITECTURE/ARCHITECTURE_MAP.md`](ARCHITECTURE/architecture-map.md)
