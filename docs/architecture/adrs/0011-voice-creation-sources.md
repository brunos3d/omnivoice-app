# ADR-0011: Voice Creation Sources

- **Status:** Accepted (architecture only — no code, no migrations, no API/runtime change)
- **Date:** 2026-06-04
- **Deciders:** Bruno Silva (product owner), architecture planning
- **Generalizes:** [ADR-0010](0010-voice-source-assets-and-automatic-variant-provisioning.md) —
  the *Voice Source Asset* becomes one Creation Source **type** (`SOURCE_ASSET`), not the
  universal origin of a Voice.
- **Relates to:** [ADR-0006](0006-voice-variant-realization-types.md) (realization types),
  [ADR-0008](0008-voice-variant-build-lifecycle.md) (build lifecycle),
  [ADR-0009](0009-artifact-versioning-and-retention.md) (artifact versioning)

> **Scope guard.** Architecture only. This ADR introduces a domain concept and a taxonomy; it
> does **not** add code, migrations, APIs, or runtime behavior. It is **not** a design of future
> providers — it documents a pattern that has **already emerged** from real provider research
> ([12-PROVIDER-VALIDATION](../12-PROVIDER-VALIDATION.md)): OmniVoice / Fish / OpenVoice are
> source-asset (cloning) based, while Kokoro is preset-voice based. PeakVox must support both
> without forcing either into the other's abstraction.

## Context

[ADR-0010](0010-voice-source-assets-and-automatic-variant-provisioning.md) established the layered
voice lifecycle:

```
Voice → Voice Source Asset → VoiceVariant → Voice Variant Artifact
```

It correctly fixed the OmniVoice-era conflation of "a voice" with "a WAV file" by elevating the
**Voice Source Asset** as the canonical source of truth. But provider validation revealed a deeper
truth that ADR-0010 did not cover: **not all Voices originate from a Source Asset.**

| Provider | How a Voice originates |
|---|---|
| OmniVoice / Fish Audio / OpenVoice | reference-audio cloning (+ embeddings) → **a Source Asset exists** |
| **Kokoro** | **provider-native preset voice packs** (`af_heart`, `af_bella`, …) → **no Source Asset, no cloning** |

And more origins are already visible on the roadmap: marketplace voices (published by another
creator), trained voices (fine-tune / LoRA / checkpoint, possibly with no single canonical WAV),
imported voices (ElevenLabs / third-party ecosystems), and platform-owned system voices.

**Therefore the Voice Source Asset is not the universal origin of a Voice — it is only one
possible way a Voice came into existence.** Kokoro is the concrete, validated proof: a Kokoro
Voice has a `voice_pack` variant but **no source WAV** and **no cloning step**. Forcing it through
the Source-Asset abstraction would either fabricate a fake source or special-case Kokoro in the
Runtime — both violate the model-agnostic invariant ([Vision](../00-VISION.md)).

## Options considered

1. **Keep Voice Source Asset as the universal origin; special-case non-cloning providers.**
   Lowest immediate change, but every preset/marketplace/trained/imported voice becomes a Runtime
   exception. The "every variant rebuilds from the Source Asset" rule (ADR-0010) breaks for voices
   that have no source asset. Name-branching on provider creeps back in. Rejected.

2. **Introduce *Voice Creation Source* as a first-class, model-independent concept that
   generalizes the Source Asset.** A Voice records *how it came to exist*; `SOURCE_ASSET` is one
   type, `PRESET_VOICE` another, etc. ADR-0010's whole mechanism becomes the behavior of the
   `SOURCE_ASSET` type. New origins are additive. **Chosen.**

3. **Model every origin as a different realization/variant type (collapse origin into variant).**
   Conflates *how a voice was created* with *how a model stores it* — two orthogonal axes. A
   marketplace voice can be realized as OmniVoice *and* Fish variants; its origin is neither.
   Rejected (see the binding rule below).

## Decision

Introduce **Voice Creation Source** as a top-level architectural concept: it describes **how a
Voice came into existence**. Creation Sources are **model-independent**. The **Voice** remains the
single universal identity layer; its `public_voice_id` is stable regardless of creation source.

### 1. Domain model

```
Voice                       universal identity (public_voice_id, stable forever)
 ├── Creation Source        HOW the voice came to exist        [THIS ADR]
 ├── Variants               per-model realizations             [ADR-0001/0006/0008]
 └── Artifacts              versioned build outputs            [ADR-0009]
```

The Creation Source is a property of the **Voice**, set once at creation, and is **not** a variant
and **not** a model. Example:

```
Voice            voice_8JXQ29K4L3
Creation Source  PRESET_VOICE
Variants         Kokoro voice_pack  (+ any future compatible variant)
```

### 2. The binding rule — Creation Source ≠ Variant

**A Voice Creation Source and a Voice Variant are different concepts and must never be merged.**

| Concept | Answers | Axis | Examples |
|---|---|---|---|
| **Creation Source** | *How did this Voice come to exist?* | origin (model-independent) | `SOURCE_ASSET`, `PRESET_VOICE`, `MARKETPLACE_VOICE` |
| **VoiceVariant** | *How does model X realize this Voice?* | realization (per-model) | OmniVoice reference_sample, Fish embedding, Kokoro voice_pack |

Origin and realization are orthogonal: one Creation Source can yield many Variants; one Variant
realization (`voice_pack`) can back voices of different origins. They never collapse into one
field.

### 3. Creation Source taxonomy (open set)

The taxonomy is **open and additive**, like the realization taxonomy
([ADR-0006](0006-voice-variant-realization-types.md) rule 3). Only the first two are validated by
real providers today; the rest are **named extension points**, documented so the model is honest
about origins already on the roadmap — **not designed here** (avoid speculative abstraction).

| Type | Meaning | Status | Example |
|---|---|---|---|
| `SOURCE_ASSET` | User-provided audio (the [ADR-0010](0010-voice-source-assets-and-automatic-variant-provisioning.md) flow). | **Real** — OmniVoice / Fish / OpenVoice | `larissa.wav`, `speaker.flac` |
| `PRESET_VOICE` | A provider-native preset; the Voice identity *wraps* an existing provider voice. No cloning, no source WAV. | **Real** — Kokoro | `af_heart`, `af_bella`, `af_sarah` |
| `MARKETPLACE_VOICE` | A Voice published by another creator; its underlying origin (asset / trained / native) is irrelevant to the consumer. | Reserved (Cloud) | a purchased/used marketplace voice |
| `TRAINED_VOICE` | A Voice produced by training (fine-tune / custom dataset / LoRA / checkpoint); may have no single canonical WAV. | Reserved | a fine-tuned brand voice |
| `IMPORTED_VOICE` | A Voice imported from an external ecosystem. | Reserved | ElevenLabs / OpenVoice / third-party import |
| `SYSTEM_VOICE` | A platform-owned voice. | Reserved | default narrator, demo voices, announcements |

The canonical list and any validation helper would live alongside the realization taxonomy when
implemented; unknown/new types are tolerated (forward-compatible) and treated as opaque by
anything that is not the owning flow.

### 4. Kokoro — the first stress test (documented explicitly)

Kokoro is the provider that proves **Voice ≠ Reference Audio**:

```
Voice            (a Kokoro voice)
Creation Source  PRESET_VOICE
Variants         Kokoro voice_pack
Source Asset     (none — no WAV, no cloning)
```

The architecture must support this **natively**, not as a Runtime special case. With Creation
Sources, it does: the Voice's origin is `PRESET_VOICE`, its realization is the `voice_pack`
([ADR-0006](0006-voice-variant-realization-types.md)), and the existing `Voice.is_preset_voice`
flag is the precursor hook for recording it. No source asset is required or fabricated.

### 5. Relationship to ADR-0010 (extended, not superseded)

[ADR-0010](0010-voice-source-assets-and-automatic-variant-provisioning.md) **remains valid and
unchanged in mechanism.** It is **reclassified** as the specialization of one Creation Source type:

- "Voice Source Asset" = the payload of the **`SOURCE_ASSET`** creation source.
- Automatic Variant Provisioning, the "rebuild every variant from the Source Asset" rule, and the
  CE block-on-missing policy all apply **specifically to `SOURCE_ASSET` voices**.

ADR-0011 generalizes; ADR-0010 becomes one case under it. Not superseded, not replaced —
**extended**.

### 6. Provisioning implications (future — no implementation)

Different creation sources will use **different provisioning strategies**. The Runtime owns the
strategy selection; this ADR only records the shape (details belong to the reserved
**ADR-0012 Variant Provisioning Policies**):

| Creation Source | Provisioning strategy (forward-looking) |
|---|---|
| `SOURCE_ASSET` | Automatic variant provisioning across compatible installed models ([ADR-0010](0010-voice-source-assets-and-automatic-variant-provisioning.md)). |
| `PRESET_VOICE` | **No build required** — the variant wraps an existing provider preset; "ensure" = verify the preset resolves. |
| `MARKETPLACE_VOICE` | Artifacts **may already exist** (published with the voice); provisioning may be import/verify rather than build. |
| `TRAINED_VOICE` | Build pipeline is **provider-specific** (training/fine-tune); long-running, likely async. |
| `IMPORTED_VOICE` | Import/translate external artifacts; strategy depends on the source ecosystem. |
| `SYSTEM_VOICE` | Platform-provisioned; typically preset-like or prebuilt. |

### 7. Voice Library implications (future — no implementation)

The Voice Library should expose a Voice's **Origin** as a model-independent label, **without**
exposing provider-specific complexity (realizations/artifacts stay hidden, per
[ADR-0004](0004-voice-variant-model-separation.md)):

```
Larissa              Origin: Source Audio
af_heart             Origin: Preset Voice
Marketplace Narrator Origin: Marketplace Voice
```

Origin is a display affordance; it never leaks variant/artifact internals.

### 8. Cloud / marketplace implications (future — no implementation)

The Cloud Marketplace will lean heavily on this concept. A `MARKETPLACE_VOICE` may itself
originate from a creator upload (`SOURCE_ASSET`), a `TRAINED_VOICE`, a licensed voice pack, or a
partner provider — **the consumer never cares**. Consumers interact only with `public_voice_id`;
the creation source stays an internal concern. This preserves the public-contract stability the
Vision requires.

## Consequences

- **Positive:**
  - Voice origin is finally a named, model-independent axis distinct from realization — Kokoro and
    future non-cloning/marketplace/trained voices fit **natively**, with no Runtime special cases.
  - ADR-0010's strong "rebuild from the Source Asset" guarantee is correctly **scoped** to
    `SOURCE_ASSET` voices instead of wrongly applied to all voices.
  - The public contract (`public_voice_id` + `model`) is unaffected; origin never leaks.
  - The taxonomy is open and additive, so new origins are documentation + one type, not a redesign.
- **Negative / costs:**
  - Introduces another first-class concept; the implementation phase must add a `creation_source`
    (type + reference) to the Voice data model and migrate existing voices to `SOURCE_ASSET`
    (deferred — not in this ADR).
  - The reserved taxonomy types invite premature design; this ADR deliberately marks them
    *reserved* and forbids designing providers here.
- **Follow-ups / reserved future ADRs** (named only — **do not define them here**):
  - **ADR-0012 — Variant Provisioning Policies** (per-creation-source provisioning strategies).
  - **ADR-0013 — Model Categories** (classifying providers, e.g. cloning vs preset vs training).
  - **ADR-0014 — Marketplace Voice Publishing**.
  - **ADR-0015 — Imported Voice Ecosystem**.
  - Implementation phase: the `creation_source` data model + backfill to `SOURCE_ASSET`; the
    `PRESET_VOICE` "no-build" provisioning branch when Kokoro is integrated.
