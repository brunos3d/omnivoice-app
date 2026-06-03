# TTS Auto-Configuration — Design Spec

**Date:** 2026-06-03
**Status:** Implemented
**Sub-project:** E of the OmniVoice Phase 2 platform initiative
**Depends on:** A (voice metadata), B (language registry), C/D (library + API)

---

## Context

Phase 15 of the brief: when a user selects a voice, automatically apply its metadata to
the Text-to-Speech screen — language, generation defaults (preset), and voice design /
style tags — rather than only changing the selected voice. Behavior must be consistent
between the UI and the public API.

## Findings

The Zustand store's `setSelectedProfile` **already** applied a voice's
`generation_defaults` (inference settings) and `voice_design` (style attributes) on
selection. The only missing piece was **language**, which lived as local component state
in `app/page.tsx` and was never driven by the selected voice.

The public API already applies a voice's defaults + language at generation time
(`/api/v1/text-to-speech`, sub-project D), so closing the UI gap makes the two paths
consistent.

## Changes

- **Store** (`store/use-store.ts`): lift TTS language into the store as
  `ttsLanguage: string | null` (OmniVoice id, null = Auto) with `setTtsLanguage`.
  `setSelectedProfile` now also sets `ttsLanguage = profile.language_code ?? <current>`
  — a voice with a language auto-selects it; a voice without one leaves the current
  language untouched.
- **TTS page** (`app/page.tsx`): read `ttsLanguage`/`setTtsLanguage` from the store
  instead of local state. The `LanguageCombobox`, the generation request, and the
  language-aware Quick Prompts all consume the store value.

Generation defaults, GPU flag, and `voice_design` continue to auto-load via the existing
`setSelectedProfile` logic; the flat `instruct` string is derived from `voice_design` at
submit time (unchanged).

## Consistency (UI ↔ API)

| Aspect | UI (TTS page) | API (`/api/v1/text-to-speech`) |
|---|---|---|
| Inference defaults | from `voice.generation_defaults` | from `voice.generation_defaults` |
| Voice design → instruct | `buildInstruct(voice_design)` | `", ".join(voice_design)` |
| Language | `voice.language_code` (overridable) | `payload.language ?? voice.language_code` |
| Usage counting | increments on generate | increments on generate |

## Risks & notes

- Selecting a voice overrides any manually-chosen language. This is the intended
  "apply all voice metadata" behavior; users can re-pick afterward.
- Legacy voices without `language_code` don't change the language (no silent reset);
  they can still be matched by display name elsewhere via `getLanguageByName`.

## Success criteria

- Selecting a voice with a language auto-selects it in the TTS language picker.
- Inference settings + voice design continue to auto-load (already true).
- UI and API apply the same voice metadata.
- `tsc`, lint, and build remain clean.
