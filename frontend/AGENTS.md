<!-- BEGIN:nextjs-agent-rules -->

# Next.js: ALWAYS read docs before coding

Before any Next.js work, find and read the relevant doc in `node_modules/next/dist/docs/`. Your training data is outdated — the docs are the source of truth.

<!-- END:nextjs-agent-rules -->

# PeakVox frontend rules (model-agnostic UI)

This app is evolving into **PeakVox**, a model-agnostic Universal Voice Runtime. See
`../docs/architecture/` (start with `00-VISION.md`). The UI must stay model-agnostic:

1. **Address voices by `public_voice_id`** — it is a permanent public contract. A voice is a
   portable asset, **not tied to a model**. Never assume "this voice's model."
2. **Never surface model internals** — embeddings, checkpoints, variant formats, or other
   model-specific artifacts must not appear in the UI or types
   ([ADR-0004](../docs/architecture/adrs/0004-voice-variant-model-separation.md)).
3. **Capability-driven controls.** Render model-specific controls (singing, emotion tags, voice
   design, streaming) **only when the selected model declares the capability** — read the model's
   `ModelCapabilities`; never hard-code per-model conditionals
   ([ADR-0003](../docs/architecture/adrs/0003-model-capability-contract.md)).
4. **Generation is `voice + model + text`.** Selecting a different model must not change the
   voice or the integration shape.
5. **Commercial nav is feature-flag gated.** Marketplace / Creator / Billing surfaces are
   Cloud-only — hidden in Community Edition. Gate them on the edition feature flags, don't
   assume they're always present.
