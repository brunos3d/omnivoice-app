# ADR-0003: Model Capability Contract

- **Status:** Accepted
- **Date:** 2026-06-03
- **Deciders:** Bruno Silva (product owner), architecture planning

## Context

PeakVox is a model-agnostic [Universal Voice Runtime](../00-VISION.md): many providers
(OmniVoice, OmniVoice Singing, Fish Audio, Kokoro, OpenVoice, and future engines) plug in
behind one [`ModelAdapter`](../10-RUNTIME_ARCHITECTURE.md) contract. These models differ in
what they can do — some clone, some sing, some convert voice, some stream, some only do basic
TTS. Four independent consumers need to know a model's feature surface:

- the **Runtime** (validate a request before loading weights; route `auto`),
- the **public API** (reject unsupported requests with a stable error),
- the **UI** (show/hide controls — singing, emotion tags, voice design),
- the **Marketplace** (filter voices by model compatibility; show which engines a voice supports).

If feature detection is **ad-hoc** — scattered `if model_id == "omnivoice"` checks, inferred
from model names, or duplicated per consumer — then adding the second, third, and tenth model
causes **capability drift**: inconsistent behavior across surfaces, silent failures, and
churn in code that should be stable. The runtime's core promise (adding a model never changes
public APIs/UI/marketplace) cannot hold without a single, declared source of truth.

A partial `ModelCapabilities` already exists (`supports_tts`, `supports_voice_cloning`,
`supports_emotions`, `supports_singing`, `supports_streaming`, `supports_api`). It must be
**frozen as a contract and made forward-compatible before multiple providers are added.**

## Options considered

1. **Ad-hoc per-consumer detection.** Each surface infers capabilities (name matching, feature
   probing, hard-coded maps). Fastest now; guarantees drift and coupling later. Rejected.

2. **A frozen, declared Model Capability Contract.** Every adapter declares its capabilities
   via `get_capabilities()`; all four consumers read that one contract; it is versioned and
   forward-compatible. Higher discipline now; eliminates drift. **Chosen.**

3. **Per-capability plugin negotiation at call time.** Maximum flexibility (capabilities probed
   dynamically per request). Over-engineered for the foreseeable models; defers no real risk
   that option 2 doesn't already cover. Rejected (YAGNI).

## Decision

Adopt **Option 2**. Model capabilities are a **frozen, declared, versioned contract**. An
adapter **declares** its capabilities; it never lets a consumer infer them. The Runtime, API,
UI, and Marketplace consume this one contract.

### Capability set (the contract)

Boolean capabilities (declared per model; default `False` unless the adapter sets `True`):

```
supports_tts                 supports_voice_design
supports_voice_cloning       supports_streaming
supports_voice_conversion    supports_multilingual
supports_singing             supports_speaker_embeddings
supports_emotion_tags        supports_custom_training
supports_reference_audio     supports_batch_generation
```

(`supports_emotion_tags` supersedes the legacy `supports_emotions`; `supports_api` is retained
as a transport flag. The current `ModelCapabilities` is the **v1 subset**; this ADR defines the
canonical superset, added forward-compatibly in Phase 2 — complementary to the
requirements/license/provider metadata of [ADR-0002](0002-model-as-first-class-entity.md).)

### Versioning strategy

- `ModelCapabilities` carries an explicit `capability_version` (integer, starts at `1`).
- **New capabilities are additive** and default to `False`. Adding one bumps the version but
  does **not** break existing adapters or stored model rows — absent fields read as `False`.
- A capability is **never repurposed**. To change meaning, add a new capability and deprecate
  the old (kept readable). This mirrors the additive-migration discipline used everywhere else.

### Forward compatibility & unknown-capability handling

- **Readers tolerate unknown capabilities:** a consumer on `capability_version = N` ignores
  capabilities it doesn't know from a model declaring version `N+1` (no crash, no guess).
- **Writers never assume presence:** code checks a capability with a safe default of `False`
  (`getattr(caps, "supports_x", False)`), so older models simply lack newer features.
- **Absent = unsupported.** The safe default everywhere is "not supported."

### Validation rules

- **Runtime validation:** before loading weights, the runtime checks the request against the
  model's declared capabilities. A mismatch (e.g. singing requested on a model without
  `supports_singing`) is rejected **up front** — never a half-run that fails inside inference.
- **API validation:** the public API maps a capability mismatch to a stable `422` with a
  machine-readable reason (`model does not support 'singing'`). The error contract is part of
  the stable API surface ([API §3](../04-API_ARCHITECTURE.md)).
- **UI adaptation rules:** the UI renders controls **only** for declared capabilities — singing
  controls appear only when `supports_singing`, emotion-tag pickers only when
  `supports_emotion_tags`, the Voice Design builder only when `supports_voice_design`. The UI
  reads the contract; it contains no per-model conditionals.
- **Marketplace rules:** listings filter and badge by capability (e.g. "supports singing"), and
  voice↔model compatibility is computed from capabilities + available VoiceVariants — never
  from provider names.

## Consequences

- **Positive:** no capability drift as providers multiply; one source of truth across Runtime,
  API, UI, Marketplace; `auto` routing becomes possible (the router scores models by declared
  capability fit); adapters are self-describing; UI/marketplace adapt to new models with zero
  per-model code.
- **Negative / costs:** every adapter must accurately declare capabilities (a small, explicit
  burden); the contract must be governed (additions are deliberate, versioned).
- **Follow-ups:** Phase 2 adds the superset + `capability_version` to `ModelCapabilities`
  forward-compatibly and surfaces it via `get_capabilities()` on the adapter
  ([Runtime §6](../10-RUNTIME_ARCHITECTURE.md)); UI/API/Marketplace consume it in their
  respective phases. Ties to [ADR-0001](0001-voice-variant-split.md) (a variant's existence for
  a model is orthogonal to the model's capabilities) and [ADR-0004](0004-voice-variant-model-separation.md)
  (capabilities belong to the Model, never to the Voice).
