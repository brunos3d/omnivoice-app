# Task 29 — Public API 2.0 Audit & Findings

> **Scope:** the public, key-authenticated `/api/v1` surface and the frontend developer portal
> (`/api`, `/api/keys`, `/api/voices`, `/api/usage`), evaluated against PeakVox's current
> internal architecture (Voice → Model → Runtime → RuntimeVariant → Generation). Goal: make the
> API a first-class, self-discoverable, **voice-first** developer platform without breaking
> existing clients.
>
> **Date:** 2026-06-11 · **Task:** 29 · **Decision output:** ADR-0020 (Public API 2.0).

---

## A.1 What exists today (evidence)

### Public API (`backend/app/api/v1.py`, mounted at `/api/v1`)

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/v1/voices` | List own voices. Cursor-paginated (`limit` ≤ 100). Returns `{voiceId, name, language}`. |
| `GET` | `/api/v1/voices/{voiceId}` | Voice detail: `voiceId, name, language, languageCode, description, usageCount, characteristics, createdAt`. |
| `POST` | `/api/v1/voices` | Create a voice from a reference upload (10s server-side cap). |
| `DELETE` | `/api/v1/voices/{voiceId}` | Delete a voice. |
| `POST` | `/api/v1/text-to-speech` | Generate. `?response=stream\|url`. Body: `{voiceId, text, modelId?, language?, format?}`. |

Auth: `Authorization: Bearer ov_live_…` or `X-API-Key` (`require_api_key`,
`backend/app/services/api_keys.py`). Rate limiting is a no-op seam in CE
(`enforce_rate_limit`).

Request/response schemas live in `backend/app/schemas/api.py`
(`TextToSpeechRequest`, `V1Voice`, `V1VoiceDetail`, `V1VoiceList`,
`TextToSpeechUrlResponse`). Field naming is **camelCase** by deliberate convention.

### Internal (app-only) surfaces that have no public-API equivalent

- **Models / capabilities:** `GET /models`, `GET /models/{id}`, `GET /models/{id}/capabilities`
  (via `_descriptor_payload`), `GET /models/{id}/tags`, `GET /models/{id}/status`
  (`backend/app/api/models.py`). The descriptor already carries `capabilities`
  (`ModelCapabilities`, ADR-0003), `settings_schema` (`SettingsSchema` — code-declared generation
  parameters), `supported_languages`, `editions`, `requirements`, `license`.
- **Runtimes & RuntimeVariants:** `GET /runtimes`, `GET /runtimes/{id}`,
  `GET /api/models/with-runtimes` (composed view) — the latter already returns a
  **public-safe** `variants` array per runtime via `_variants_payload`
  (`backend/app/api/runtime_api.py`), exposing `{id, name, description, trust, source_url,
  source_type, model_id, is_default, capabilities}` and **deliberately omitting** checkpoint
  internals (`source_ref`, `format`, `digest`) per ADR-0004 §6.
- **VoiceVariants (internal realizations):** `GET /voices/{id}/variants`,
  `GET /variants/summary` (`variants.py`, `variants_summary.py`). These are **internal** by
  constitutional rule and must never appear on `/api/v1`.

### Frontend developer portal (`frontend/src/app/api/…`)

Minimal: `page.tsx` (79 lines), `voices/page.tsx` (76), `keys/page.tsx` (155),
`usage/page.tsx` (58); helpers `components/api/CodeTabs.tsx`, `UseInApiDialog.tsx`. Code
examples are limited (cURL/JS/Python in the in-app dialog); there is no endpoint reference, no
model/variant/capability discovery, and no Go/C# examples.

---

## A.2 The terminology trap: two different "variants"

The single most important finding. PeakVox has **two unrelated concepts that share the word
"variant"**, and the public API must keep them apart:

| | **VoiceVariant** | **RuntimeVariant** |
|---|---|---|
| What | A Voice's model-specific *realization* (embeddings/checkpoints/refs). | A model *variation* served by one runtime image (base / singing / pt-br / narrator). |
| ADR | ADR-0001, ADR-0004 | ADR-0018, ADR-0019 |
| Public? | **Never** (Constitution Art. II §6) | **Yes** — this is the public `variantId`. |
| On-disk | `voice_variants` table | `runtime-registry/<runtime>/variants/<id>.json` (`kind: RuntimeVariant`) |

The task's `GET /api/v1/models/{modelId}/variants` and the generation `variantId` refer to
**RuntimeVariants**, not VoiceVariants. The audit's recommendations and ADR-0020 use the term
**RuntimeVariant** precisely, and the public field is named `variantId` (a RuntimeVariant id
such as `base`, `singing`).

---

## A.3 Current limitations

1. **No discovery.** The public API exposes voices + generate only. A developer cannot list
   models, list a model's RuntimeVariants, read capabilities, or check voice↔model
   compatibility without reading source code. There is no public OpenAPI surfacing these.
2. **Model selection is opaque.** `modelId` is accepted on TTS, but there is no public endpoint
   to *discover* valid model ids, their capabilities, languages, or default. A caller must
   already know `omnivoice-base`.
3. **RuntimeVariant selection is absent from the public contract.** The platform resolves a
   default runtime/variant internally, but a caller cannot select `variantId` (e.g. `singing`)
   through `/api/v1`. The capability already exists internally (composed view) but is not
   public.
4. **Generation settings are not formally modeled on the public API.** The TTS endpoint
   silently applies the voice's saved defaults and a fixed `gen_params` dict
   (`num_step`, `guidance_scale`, `speed`, `duration`, `t_shift`, `denoise`). Callers cannot
   override platform-level settings (speed, language already partially) or pass model-specific
   parameters. Internally, `ModelDescriptor.settings_schema` (`SettingsSchema`/`ParameterSchema`)
   already declares these per model — but it is not exposed publicly and not accepted on the
   public request.
5. **Provider-specific parameters have no pass-through.** Adding a model parameter (e.g.
   `cfg_scale`, `sampling_steps`) would today require changing the public schema. There is no
   flexible `providerSettings` escape hatch.
6. **Capability discovery is internal-only.** `ModelCapabilities` (ADR-0003) is rich and
   already the single source of truth, but `/api/v1` never returns it, so consumers cannot
   branch on `supports_singing`, `supports_reference_audio`, `supports_voice_optional`, etc.
7. **Compatibility is not expressible.** A caller cannot ask "which models/variants work with
   this voice?" There is no `compatible-models` / `compatible-variants` endpoint.
8. **Identifier guarantees are undocumented publicly.** `public_voice_id` stability is a
   constitutional invariant (Art. II §5) but is not stated in the public contract; model ids
   and variant ids have no published stability promise.
9. **Portal is a stub, not a developer portal.** No endpoint reference, no response/error
   schemas, limited languages, no interactive request builder.

## A.4 Missing concepts (to introduce)

- Public **Model resource** (`GET /api/v1/models`, `/models/{id}`) — id, name, description,
  default flag, languages, capabilities, settings schema (public-safe).
- Public **RuntimeVariant resource** (`GET /api/v1/models/{id}/variants`,
  `/variants/{variantId}`) — id, name, description, trust, default flag, capabilities. No
  checkpoint internals.
- Public **Capabilities resource** (`GET /api/v1/models/{id}/capabilities`).
- **Compatibility** (`GET /api/v1/voices/{id}/compatible-models`, `/compatible-variants`).
- **Generation v2 request fields** (additive): `variantId`, `generationSettings` (platform-level,
  capability-gated), `providerSettings` (flexible, model-specific pass-through).

## A.5 Breaking-change risks (and how Task 29 avoids them)

- **`/api/v1` and `public_voice_id` are stable by constitution (Art. VIII).** All Task 29
  changes are **additive**: new read-only endpoints + new **optional** request fields with
  identical default behavior when omitted. The minimal `{voiceId, text}` request keeps working
  byte-for-byte.
- **Do not leak model internals.** Public model/variant payloads must mirror the existing
  `_variants_payload` discipline (no `source_ref`/`format`/`digest`); never expose VoiceVariant
  rows. (Constitution Art. II §6, ADR-0004 §6.)
- **`providerSettings` must be a pass-through, not a typed contract.** Typing it per model
  re-couples the public API to providers — exactly what the platform forbids. It stays a free
  dict, validated/ignored by the adapter, so adding a model parameter never changes the API.
- **Capability-gating, not hardcoding.** `generationSettings` must be validated against the
  model's declared `settings_schema`/`capabilities`, never a hardcoded per-model branch
  (ADR-0003; Constitution Art. III §10).

## A.6 Future-extensibility concerns

- **Cloud:** the same identifiers and capability contract carry into Cloud unchanged; only the
  auth/rate-limit seams (already present) light up. Discovery endpoints become per-account
  scoped; nothing in the shape changes.
- **`model="auto"` routing (Vision):** a future capability-based router is a forward-compatible
  extension of the *same* generate endpoint — `modelId`/`variantId` optional, resolved by the
  runtime. The Task 29 contract leaves room for it (both already optional).
- **Streaming:** `supports_streaming` exists in the capability contract; a future streaming
  response mode is additive (`?response=stream` already exists for non-chunked streaming).
- **OpenAPI:** FastAPI already generates `/openapi.json` + `/docs`. Task 29 should enrich the
  `/api/v1` operations (summaries, descriptions, response models, tags) so the generated schema
  is genuinely usable — preferred over hand-maintained schema exports.

---

## A.7 Recommendations → ADR-0020

1. Formalize **identifiers** (Phase B): `public_voice_id` (stable, public, immutable);
   **Model id** (stable, human-readable, runtime-independent — `omnivoice-base`, `f5-tts-base`,
   `kokoro-base`); **RuntimeVariant id** (stable, human-readable, checkpoint/FS-independent —
   `base`, `singing`, `pt-br`).
2. Add **read-only discovery endpoints** (Phase C/E/I) on `/api/v1`: models, model detail,
   variants, variant detail, capabilities, voice compatible-models/compatible-variants.
3. Specify **Generation v2** (Phase D) as additive optional fields: `variantId`,
   `generationSettings` (capability-gated platform settings), `providerSettings` (flexible
   model pass-through). Keep `{voiceId, text}` minimal.
4. Make settings **capability-driven** (Phase E): models declare; consumers discover; the API
   validates against the declared schema, never hardcodes.
5. Modernize the **developer portal** (Phase F) and lean on **FastAPI OpenAPI** (Phase G).
6. Record all of the above in **ADR-0020** (Phase H) with CE/Cloud implications.

Implementation in this task (Phase I) is strictly **low-risk and backward-compatible**:
additive read-only endpoints, additive optional request fields, OpenAPI metadata, and portal
improvements. No existing endpoint shape changes.

---

**Related:** [`../../DECISIONS/adr-0020-public-api-2.0.md`](../../DECISIONS/adr-0020-public-api-2.0.md) ·
[`../../ARCHITECTURE/api-architecture.md`](../../ARCHITECTURE/api-architecture.md) ·
[ADR-0003](../../DECISIONS/adr-0003-model-capability-contract.md) ·
[ADR-0004](../../DECISIONS/adr-0004-voice-variant-model-separation.md) ·
[ADR-0018](../../DECISIONS/adr-0018-runtime-variants-architecture.md) ·
[Constitution](../../CONSTITUTION.md)
