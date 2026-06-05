# ADR-0004: Voice, VoiceVariant, and Model are three separate concepts

- **Status:** Accepted
- **Date:** 2026-06-03
- **Deciders:** Bruno Silva (product owner), architecture planning

## Context

PeakVox is a [Universal Voice Runtime](../CONTEXT/VISION.md) where **voices are portable assets**
and **models are interchangeable engines**. The single biggest threat to that vision is
**conceptual collapse** — code, APIs, UI, or marketplace features that quietly treat a voice
as belonging to a model, or that leak a model's implementation artifacts into the public
surface. The legacy `VoiceProfile` did exactly this (it fused a voice's identity with
OmniVoice-specific artifacts). [ADR-0001](adr-0001-voice-variant-split.md) split identity from
realization, and [ADR-0002](adr-0002-model-as-first-class-entity.md) made Model first-class. This
ADR **formalizes the three-way separation as a binding architectural rule** so future
decisions cannot re-couple them.

These three concepts are **related but never the same thing**:

### Voice — a PeakVox asset

A Voice is the **public identity of a speaker**, owned by PeakVox (and its creator), **not by
any model**. It contains: public Voice ID, name, description, language metadata, creator and
ownership metadata, marketplace metadata, visibility settings, usage statistics.

The **Voice ID is a permanent public contract**. `voice_8JXQ29K4L3` must survive: model
upgrades, model replacements, runtime upgrades, infrastructure changes, voice-variant
regeneration, and cloud migrations.

### VoiceVariant — a model-specific implementation of a Voice

A VoiceVariant is **how one Model realizes a Voice**: its embeddings, checkpoints, training
artifacts, reference formats, and preprocessing outputs. These implementation details **belong
to the Variant and must never leak into the public API**. **Variants are replaceable; Voice IDs
are not.**

### Model — an inference engine

A Model is a provider/engine (OmniVoice, OmniVoice Singing, Fish Audio S2, Kokoro, OpenVoice).
Models **consume VoiceVariants and generate outputs**. A Model may be installed, upgraded,
deprecated, replaced, or removed **without changing the public Voice identity**.

### The relationship

```
Voice ──< VoiceVariant >── Model

Voice
└── voice_8JXQ29K4L3
Variants
├── OmniVoice Variant
├── OmniVoice Singing Variant
├── Fish Audio Variant
└── Kokoro Variant
Models
├── OmniVoice
├── OmniVoice Singing
├── Fish Audio
└── Kokoro

Runtime resolves:  Voice ID + Selected Model → VoiceVariant → Inference
```

## Options considered

1. **Keep them conceptually fused / partially merged** (e.g. a voice "for a model", or exposing
   variant artifacts on the voice API). Simpler short-term data flow; structurally guarantees
   model coupling and breaks portability the moment a second provider arrives. Rejected.

2. **Three strictly separate concepts with explicit boundary rules** binding every layer
   (domain, data, API, runtime, marketplace). More upfront discipline; preserves the runtime
   vision permanently. **Chosen.**

## Decision

**Voice, VoiceVariant, and Model are three separate concepts and must remain separated across
every layer of PeakVox.** The Runtime is the only component that joins them, resolving
`Voice ID + Selected Model → VoiceVariant → Inference`
([Runtime §4](../ARCHITECTURE/runtime-architecture.md)).

### Binding architectural rules (normative)

1. **No public API exposes model-specific voice internals.** Embeddings, checkpoints, training
   formats, variant formats, and model internals never appear in `/v1` responses. The public
   surface is Voice (`public_voice_id`) + Model id only.
2. **No feature assumes a Voice belongs to a specific model.** Voice identity, library,
   ownership, and metadata are model-agnostic. Code may not branch on "this voice's model."
3. **No marketplace feature is tied to a specific provider.** Listings reference Voices;
   model/provider compatibility is derived from capabilities + available variants
   ([ADR-0003](adr-0003-model-capability-contract.md)), never hard-coded to a provider.
4. **The Voice ID is immutable and provider-independent.** It survives variant regeneration,
   model replacement, and infrastructure/cloud changes.
5. **Variant artifacts are encapsulated.** They are read only by the owning Model's adapter,
   via the Runtime — never by API handlers, UI, or marketplace code.
6. **Developers never need model internals.** The contract is `voice_id + model + text`; the
   Runtime abstracts embeddings/checkpoints/variant formats entirely.

### What developers see (must remain valid as models are added)

```python
peakvox.tts.generate(voice_id="voice_8JXQ29K4L3", model="omnivoice",      text="Hello world.")
peakvox.tts.generate(voice_id="voice_8JXQ29K4L3", model="fish-audio-s2",  text="Hello world.")
peakvox.tts.generate(voice_id="voice_8JXQ29K4L3", model="kokoro",         text="Hello world.")
```

Same API, same Voice ID, same integration — different model. Only the engine changes; the Voice
remains the same.

## Consequences

- **Positive:** model coupling is structurally prevented; Voice IDs are durable public
  contracts; the marketplace and creator economy rest on portable assets; new models (and whole
  new [model categories](../ARCHITECTURE/runtime-architecture.md#12-model-classification)) integrate
  without touching the public surface; the runtime vision is protected by an explicit rule, not
  just convention.
- **Negative / costs:** requires ongoing discipline in reviews (reject any PR that leaks
  variant internals or couples a voice to a model); a resolution indirection (Voice→Variant)
  on every generation.
- **Follow-ups:** enforced by [Domain §1–§5](../ARCHITECTURE/domain-architecture.md), the
  [Data model](../ARCHITECTURE/data-architecture.md) (separate `voices` / `voice_variants` / `models`
  tables), the [API contract](../ARCHITECTURE/api-architecture.md), the
  [Runtime](../ARCHITECTURE/runtime-architecture.md), and the
  [Marketplace](../ARCHITECTURE/marketplace-architecture.md). Builds directly on
  [ADR-0001](adr-0001-voice-variant-split.md) and [ADR-0002](adr-0002-model-as-first-class-entity.md);
  capabilities-belong-to-Model is governed by [ADR-0003](adr-0003-model-capability-contract.md).
