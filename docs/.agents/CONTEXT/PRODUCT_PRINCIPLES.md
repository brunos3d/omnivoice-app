# Product Principles

Derived from the vision and the binding architectural rules. These guide product decisions;
the [`../CONSTITUTION.md`](../CONSTITUTION.md) makes them enforceable.

1. **Model-agnostic by default.** Never surface model internals (embeddings, checkpoints,
   variant formats) in the UI, types, or public API. A voice is never "a model's voice."
2. **Address voices by `public_voice_id`.** It is a permanent public contract. UIs and APIs
   speak Voice + Model, never VoiceVariant.
3. **Capability-driven UI.** Render model-specific controls (singing, emotion tags, voice
   design, streaming) **only** when the selected model declares the capability. Never hard-code
   per-model conditionals.
4. **Generation is `voice + model + text`.** Switching models must not change the voice or the
   integration shape.
5. **One integration, forever.** Adding a model never breaks an existing integration.
6. **CE is genuinely useful alone.** The infrastructure layer stands on its own; the ecosystem
   is additive.
7. **Commercial surfaces are feature-flag gated.** Marketplace / Creator / Billing are
   Cloud-only and hidden in CE — never assume they are present.
8. **Honesty about validation.** Distinguish "the platform can orchestrate this" from "a real
   model runs this." Never claim provider support that is not provider-validated.

---

**Related:** [`../../frontend/AGENTS.md`](../../../frontend/AGENTS.md) ·
[`../CONSTITUTION.md`](../CONSTITUTION.md) · [`VISION.md`](VISION.md)
