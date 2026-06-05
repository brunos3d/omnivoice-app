# PeakVox Runtime Validation (Phases 3.7.5–3.10) — Design

**Status:** Accepted; executed with TDD on `feat/peakvox-phase-1`.
**Goal:** eliminate architectural risk and prove PeakVox supports radically different voice
providers through one Runtime abstraction — **no** commercial/cloud work. Architecture
validation over feature expansion.

> Builds on the implemented Runtime ([10-RUNTIME](../../ARCHITECTURE/runtime-architecture.md),
> ADR-0001..0004). Adds ADR-0005 (edition-scoped model availability).

---

## Phase 3.7.5 — Runtime Exclusivity

**Problem:** generation can still reach providers/models outside the Runtime (the worker calls
`model_registry.generate`; the endpoint resolves models + validates tags directly).

**Target:** `API → PeakVoxRuntime → ModelAdapter → Provider → Inference`, with the Runtime the
*single* generation entry point.

**Changes:**
- `PeakVoxRuntime.is_generating` (delegates to the registry's single-flight lock) +
  `is_available(model_id)` / availability enforcement.
- `api/generation.py`: model resolution via `runtime.resolve_model`, tag validation via
  `runtime.validate_tags`, busy-check via `runtime.is_generating`. The worker `_process_job`
  calls `runtime.generate(...)` (ad-hoc, staged ref audio) instead of `model_registry.generate`.
- No endpoint/worker calls a provider, adapter, or model-specific generation path directly.

**Tests:** runtime busy-state; runtime ad-hoc generation; (endpoint/worker are torch-only →
`py_compile` + the runtime-level tests cover the contract).

## Edition-scoped model availability (ADR-0005)

- `Model.editions` is the authoritative availability declaration; `ModelLicense` documents the
  basis. `model_registry.list_models(edition)` already filters.
- `PeakVoxRuntime` enforces availability: resolving/generating a model not in `settings.EDITION`
  raises `ModelNotAvailableInEdition` (→ 409). No model-name branching.

**Tests:** available vs unavailable model per edition; CE-only model rejected under a `cloud`
edition; resolution unaffected for available models.

## Phase 3.8 — External Provider Validation (Fish Audio, CE-only)

**Goal:** prove a provider *outside* the OmniVoice ecosystem plugs into the Runtime with no
runtime changes. Fish Audio differs in architecture/representation/embeddings/pipeline.

**Changes:**
- `FishAudioAdapter(ModelAdapter)` — implements the full contract; `build_variant` produces a
  Fish-specific variant (embedding/reference) **encapsulated** (never exposed). Data methods from
  the descriptor. Inference delegates to a Fish provider (lazy; weights/runtime are CE concerns
  and ship `status="disabled"` until verified — same posture as Singing).
- Catalog: `fish-audio-s2` descriptor, `editions=["community"]` (CE-only per ADR-0005),
  `provider="fish-audio"`, capabilities declared (e.g. `supports_voice_cloning`,
  `supports_speaker_embeddings`-style via the contract), Fish license metadata.
- Wiring: register the adapter (provider→adapter map) + provider factory.

**Tests:** Fish adapter implements the contract; capabilities/tags from descriptor; build_variant
creates a `fish-audio-s2` variant for an existing Voice; the Runtime resolves it with **no
runtime code change**; Fish is unavailable under `cloud` edition.

## Phase 3.9 — Capability-driven generation UI

**Goal:** the UI stops assuming OmniVoice; controls derive from the selected model's declared
capabilities/tags/languages (read from `/models`). No hardcoded model-name branching.

**Changes:** a `useModelCapabilities`-style selector + capability-gated rendering of design /
singing / emotion / language controls. Foundation only — no rich editor rework.

**Tests:** lint + build; capability gating verified against model data.

## Phase 3.10 — Universal Voice Asset Validation

**Goal:** prove `Voice ≠ VoiceVariant ≠ Model` holds across *all* providers and the public
`public_voice_id` is stable across OmniVoice + Singing + Fish variants.

**Test:** one Voice ID → OmniVoice, Singing, and Fish variants via the Runtime; identity constant,
variants/providers differ; capabilities follow the Model not the Voice.

---

## Out of scope (explicitly deferred)
Auth, Billing, Creators, Marketplace, Cloud infra. Not started until Runtime Exclusivity +
External Provider Validation are complete and validated (this spec).

## Success criteria
- Generation flows **only** through the Runtime.
- A non-OmniVoice provider (Fish Audio) integrates with **no Runtime changes**.
- Model availability is edition-scoped and enforced (CE-only models rejected in Cloud).
- The UI is capability-driven.
- One stable Voice ID resolves across OmniVoice + Singing + Fish.
