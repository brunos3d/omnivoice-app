# ADR-0020: Public API 2.0 — Voice-First, Model-Aware, Variant-Aware

- **Status:** Accepted
- **Date:** 2026-06-11
- **Deciders:** PeakVox architecture (Task 29). Promotes the `/api/v1` surface from a
  voices-and-generate stub into a first-class, self-discoverable developer platform, aligned
  with the current Voice → Model → Runtime → RuntimeVariant → Generation architecture.
- **Supersedes:** none. **Extends** the public-API contract described in
  [`../ARCHITECTURE/api-architecture.md`](../ARCHITECTURE/api-architecture.md).
- **Builds on:** [ADR-0003](adr-0003-model-capability-contract.md) (Model Capability Contract),
  [ADR-0004](adr-0004-voice-variant-model-separation.md) (Voice/Variant/Model separation),
  [ADR-0005](adr-0005-edition-scoped-model-availability.md) (edition scoping),
  [ADR-0018](adr-0018-runtime-variants-architecture.md) (RuntimeVariants),
  [ADR-0019](adr-0019-variant-trust-and-community-imports.md) (variant trust).
- **Superseded by:** none.
- **Audit:** [`../VALIDATION/AUDITS/task-29-public-api-audit.md`](../VALIDATION/AUDITS/task-29-public-api-audit.md)

---

## Context

The public API (`backend/app/api/v1.py`, mounted at `/api/v1`) reflects an earlier, simpler
world: it exposes **voices** (list/get/create/delete) and **text-to-speech**, and nothing else.
Meanwhile the internal architecture has grown a Model Capability Contract, a Runtime Registry,
and RuntimeVariants — all of which are first-class internally but invisible to API consumers.

A developer integrating PeakVox today cannot, through the public API, discover models, discover
a model's RuntimeVariants, read capabilities, or determine whether a voice is compatible with a
given model. Model selection is opaque (`modelId` is accepted but undiscoverable); RuntimeVariant
selection is impossible; generation settings are silently applied from the voice's saved
defaults with no override path; and there is no flexible pass-through for model-specific
parameters. The full evidence is in the Task 29 audit.

PeakVox's north star is that the API should feel as easy to consume as OpenAI / Anthropic /
ElevenLabs / Ollama, **while preserving the Voice-First philosophy**: the minimal call is a
Voice and text. Two hard constraints bound any solution:

1. **`/api/v1` and `public_voice_id` are stable across editions and model changes**
   (Constitution Art. VIII). Changes must be additive; existing clients must keep working.
2. **No model internals on the public surface; no per-model branching** (Constitution Art. II §6,
   Art. III §10; ADR-0003, ADR-0004). The API must stay model-agnostic.

### The terminology hazard this ADR resolves

PeakVox has **two** distinct concepts that share the word "variant". This ADR fixes the public
vocabulary so they never collide:

| | **VoiceVariant** (ADR-0001/0004) | **RuntimeVariant** (ADR-0018/0019) |
|---|---|---|
| Meaning | A Voice's *model-specific realization* (embeddings/checkpoints). | A *model variation* served by one runtime image (`base`, `singing`, `pt-br`). |
| Public? | **Never.** Internal only. | **Yes.** This is the public `variantId`. |

Throughout this ADR and the public API, **`variantId` always means a RuntimeVariant id.**
VoiceVariants remain strictly internal.

---

## Decision

Evolve `/api/v1` into **Public API 2.0**: a voice-first core, with discoverable models,
RuntimeVariants, capabilities, and compatibility, and an additive Generation v2 contract that
separates platform-level **generation settings** from flexible, model-specific **provider
settings**. Everything is additive and backward-compatible.

### 1. Identifiers (Phase B)

Three public identifier classes, each **stable, human-readable, and decoupled from internal
storage**:

| Identifier | Form | Example | Guarantees |
|---|---|---|---|
| **`public_voice_id`** | `voice_` + base32 | `voice_8JXQ29K4L3` | Permanent, immutable, public. Survives model/edition/rebuild changes (Constitution Art. II §5). Public visibility is governed by the voice's scope; private voices require the owner's key. |
| **Model id** | kebab, provider-family-rooted | `omnivoice-base`, `f5-tts-base`, `kokoro-base` | Stable, human-readable, **runtime-independent**. Not tied to a runtime image, container, or filesystem path. Already the catalog `ModelDescriptor.id`. |
| **RuntimeVariant id** | short kebab, scoped to a model/runtime | `base`, `singing`, `pt-br`, `narrator` | Stable, human-readable, **checkpoint- and filesystem-independent**. Already the `RuntimeVariant.metadata.id`. `base` is the synthesized default when a runtime declares no other variants. |

Rationale: ids must be safe to print in docs, embed in code, and persist in customer
integrations for years. They therefore cannot encode checkpoints, image digests, repo paths, or
on-disk layout — all of which change. The catalog model id and the RuntimeVariant metadata id
already satisfy this; this ADR makes the guarantee **explicit and public**.

### 2. Resource model (Phase C)

Add read-only, key-authenticated resources to `/api/v1` (all additive):

```
GET /api/v1/voices                                  (exists)
GET /api/v1/voices/{voiceId}                         (exists)
GET /api/v1/voices/{voiceId}/compatible-models       (new)
GET /api/v1/voices/{voiceId}/compatible-variants     (new; ?modelId= optional filter)

GET /api/v1/models                                   (new)
GET /api/v1/models/{modelId}                         (new)
GET /api/v1/models/{modelId}/capabilities            (new)
GET /api/v1/models/{modelId}/variants                (new — RuntimeVariants)
GET /api/v1/models/{modelId}/variants/{variantId}    (new — RuntimeVariant)
```

**Public model payload** (model-agnostic, no internals): `id, name, description, isDefault,
languages, capabilities, defaultVariantId, variants[] (summary), settingsSchema` — derived from
`ModelDescriptor`. It excludes load coordinates (`repo_id`, `model_path`) and any runtime/image
internals.

**Public RuntimeVariant payload** mirrors the existing `_variants_payload` discipline:
`id, name, description, trust, isDefault, capabilities, sourceType` — and **never**
`source_ref`, `format`, or `digest` (ADR-0004 §6).

Only models available in the current edition (ADR-0005) and active are listed; inactive/other-
edition models 404 from the public surface.

### 3. Generation v2 (Phase D)

The minimal request is unchanged and **must keep working forever**:

```json
{ "voiceId": "voice_8JXQ29K4L3", "text": "Hello world." }
```

The extended request adds **only optional** fields:

```json
{
  "voiceId": "voice_8JXQ29K4L3",
  "text": "Hello world.",
  "modelId": "omnivoice-base",
  "variantId": "base",
  "language": "pt",
  "format": "wav",
  "generationSettings": { "speed": 1.1 },
  "providerSettings": { "cfg_scale": 2.0, "sampling_steps": 30 }
}
```

Resolution rules (voice-first, capability-gated):

- `modelId` omitted → platform default model (`model_registry.get_or_default`). Unchanged.
- `variantId` omitted → the model's default RuntimeVariant (`base` / synthesized base).
- `language` omitted → the voice's `languageCode`. Unchanged.
- Precedence for parameters: **`providerSettings` (most specific) > `generationSettings` >
  voice saved defaults > model defaults.** Omitting both settings objects reproduces today's
  exact behavior.

### 4. Generation settings vs provider settings (Phase D/E)

Two intentionally different fields:

- **`generationSettings` — platform-level, capability-gated, validated.** Cross-model concepts
  the platform understands: `speed`, `language`, `format`, and (where the model declares
  support) `emotion`, `style`, `temperature`, `streaming`, etc. These are **validated against
  the model's declared `settings_schema`/`capabilities`** (ADR-0003). Unsupported keys are
  rejected with a clear error or ignored per a documented policy — **never** silently branched
  on model id.

- **`providerSettings` — model-specific, flexible, pass-through.** An open object handed to the
  adapter (`cfg_scale`, `sampling_steps`, …). It is **deliberately untyped at the API boundary**
  so adding a model parameter never requires an API change. The adapter validates/ignores keys
  it does not understand. This is the escape hatch that keeps the public schema model-agnostic
  and stable while still allowing power users full control.

The split is the load-bearing design choice: it lets the API be both **simple** (voice + text),
**discoverable** (capabilities + schema), and **future-proof** (provider pass-through) without
re-coupling to any provider.

### 5. Capability-driven, not hardcoded (Phase E)

Models (and their RuntimeVariants) **declare** capabilities; consumers **discover** them; the
API **validates** against the declaration. No endpoint, validator, or UI branches on a model id
or name. The capability vocabulary is the existing `ModelCapabilities` superset (ADR-0003):
`supports_tts, supports_voice_cloning, supports_multilingual, supports_singing,
supports_voice_design, supports_emotion_tags, supports_reference_audio, supports_streaming,
supports_voice_optional, supports_batch_generation, …` plus `capability_version` for
forward-compatibility. RuntimeVariants additionally carry a per-variant `capabilities` list
(ADR-0018), surfaced on the variant resource.

Compatibility is computed from declarations, not heuristics on names: a voice is **compatible**
with a model when the model can realize/serve it — e.g. a reference-audio voice requires
`supports_reference_audio`, while `supports_voice_optional` models are compatible with no
reference. `compatible-variants` filters a model's RuntimeVariants by the same rule.

### 6. Discovery & docs (Phase G/F)

- Lean on **FastAPI's built-in OpenAPI** (`/openapi.json`, `/docs`): every `/api/v1` operation
  gets a `summary`, `description`, explicit `response_model`, and a stable tag, so the generated
  schema is genuinely usable and exportable. No hand-maintained schema file — the generated one
  is the source of truth.
- The frontend **developer portal** (`/api`, `/api/keys`, `/api/voices`, `/api/usage`) presents
  auth, base URL, the endpoint reference, request/response/error examples, supported formats,
  and **live discovery** of voice/model/variant ids and capabilities, with multi-language code
  examples (cURL, JavaScript, TypeScript, Python, Go, C#).

---

## Consequences

### Positive

- **Voice-first preserved, power exposed.** `{voiceId, text}` still works; advanced users get
  model/variant selection, settings overrides, and provider pass-through.
- **Self-discoverable.** A developer can list voices, models, variants, read capabilities, and
  check compatibility without reading source — via the API and `/docs`.
- **Model-agnostic and stable.** `providerSettings` pass-through + capability gating mean new
  models and new parameters never force an API change. `/api/v1` and `public_voice_id` stay
  stable (Art. VIII).
- **Cloud-ready.** Identical identifiers and capability contract carry into Cloud; only the
  existing auth/rate-limit seams activate. Discovery becomes account-scoped with no shape change.

### Negative / trade-offs

- `providerSettings` is untyped at the boundary — power at the cost of compile-time safety. This
  is intentional and bounded by adapter-side validation; the alternative (typed per-model) is
  forbidden by the model-agnostic invariant.
- More surface area to keep documented and tested. Mitigated by deriving payloads from existing
  descriptors and reusing the composed view's public-safe projection.

### Edition implications

- **Community Edition:** all discovery + Generation v2 endpoints are available; rate limiting is
  a no-op seam; voices are owned by the local owner. Model management stays operator/local.
- **PeakVox Cloud:** the same contract, with the auth seam (per-account keys, scopes) and the
  rate-limit seam (per-key quotas) activated, and discovery scoped per account. No new public
  shape; Cloud is wiring, not redesign (Constitution Art. V).

### Backward compatibility

All Task 29 changes are additive: new read-only endpoints and new **optional** request fields
whose omission reproduces current behavior exactly. No existing endpoint, field, or response
shape changes. Existing API consumers continue working unchanged.

---

## Implementation status (Task 29, Phase I — low-risk subset)

Shipped in this task (additive, backward-compatible):

- Read-only discovery endpoints on `/api/v1`: `models`, `models/{id}`,
  `models/{id}/capabilities`, `models/{id}/variants`, `models/{id}/variants/{variantId}`,
  `voices/{id}/compatible-models`, `voices/{id}/compatible-variants`.
- Generation v2 request fields on `POST /api/v1/text-to-speech`: optional `variantId`,
  `generationSettings`, `providerSettings`, merged into generation params with the documented
  precedence; behavior identical when omitted.
- OpenAPI metadata (summaries/descriptions/response models/tags) on the public operations.
- Modernized developer portal with endpoint reference, discovery, and multi-language examples.

Deferred (future ADRs / tasks): server-side streaming response mode, `model="auto"` routing,
batch generation endpoint, per-key scopes/quotas (Cloud).

---

**Related:** [`../ARCHITECTURE/api-architecture.md`](../ARCHITECTURE/api-architecture.md) ·
[`../CONSTITUTION.md`](../CONSTITUTION.md) · [`../CONTEXT/VISION.md`](../CONTEXT/VISION.md) ·
[ADR-0003](adr-0003-model-capability-contract.md) · [ADR-0004](adr-0004-voice-variant-model-separation.md) ·
[ADR-0018](adr-0018-runtime-variants-architecture.md) · [ADR-0019](adr-0019-variant-trust-and-community-imports.md)
