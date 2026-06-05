# Glossary

Canonical definitions. Fuller treatment in [`../DOMAIN_MODEL.md`](../DOMAIN_MODEL.md).

| Term | Definition |
|---|---|
| **PeakVox** | The Universal Voice Runtime + voice ecosystem platform. The product is the runtime, not any model. |
| **Voice** | A portable, model-agnostic identity and economic asset. Addressed by `public_voice_id`. |
| **`public_voice_id`** | The permanent, immutable public identifier for a Voice. Survives across models, editions, rebuilds. |
| **VoiceVariant** | A model-specific realization of a Voice (the artifacts one model needs). Internal; never on the public API. |
| **VoiceVariantArtifact** | A versioned snapshot of a variant's realized artifacts; supports rollback and retention. |
| **VoiceSourceAsset** | The origin material (e.g. reference WAV + provenance) for a `SOURCE_ASSET` voice. |
| **Creation Source** | A Voice's origin type: `SOURCE_ASSET`, `PRESET_VOICE`, and reserved future types. Orthogonal to VoiceVariant. |
| **Model** | An interchangeable inference engine (provider). First-class, persisted, with declared capabilities and metadata. |
| **ModelAdapter** | The contract through which a model integrates with the Runtime. Nothing above this line imports a model implementation. |
| **ModelCapabilities** | The declared, frozen capability superset for a model. Capabilities are declared, never inferred from model id/name. |
| **PeakVoxRuntime** | The single, model-agnostic generation entry point: resolves Voice+Model→Variant, validates, orchestrates inference. |
| **Generation / GenerationJob** | One inference request (`voice + model + text` → audio). CE: fire-and-forget job, polled via `GET /jobs/{id}`. |
| **Edition** | CE (infrastructure, self-hosted) vs Cloud (ecosystem, managed). Models are edition-scoped. |
| **CE** | Community Edition — the infrastructure layer. |
| **Cloud** | PeakVox Cloud — the ecosystem layer (marketplace, creators, billing, auth). |
| **Architecture-validated** | The platform can represent/orchestrate a concept, proven by automated tests. |
| **Provider-validated** | A real model runs end-to-end (installs, loads, builds a variant, generates audio). |
| **Schema-ready** | Commercial domain models/tables/boundaries exist in CE behind feature flags, disabled — never forked. |
| **ADR** | Architecture Decision Record. Immutable once accepted; superseded by new ADRs. |
| **SDD** | Spec-Driven Development (Superpowers): Brainstorm → Spec → Design → Tasks → Implementation → Validation → Review → Merge. |

---

**Related:** [`../DOMAIN_MODEL.md`](../DOMAIN_MODEL.md) · [`../DECISIONS/ADR_INDEX.md`](../DECISIONS/ADR_INDEX.md)
