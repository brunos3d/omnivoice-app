# N3 — Model-Scoped Generation Settings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute sub-phases sequentially. Each sub-phase commit must be independently verifiable.

**Goal:** Replace flat `generationSettings: GenerationSettings` with `modelSettings: Record<string, Record<string, unknown>>` keyed by `model_id`, so each model has its own parameter set. Filter generation requests to only send params declared in the model's `settings_schema`.

**Architecture:** Move from hardcoded OmniVoice-centric settings to a generic key-value store. Models declare parameters via `settings_schema`. `DynamicSettingsForm` already accepts `Record<string, unknown>`. `voiceDesign` and `useGpu` remain separate store fields (not per-model).

**Migration pattern:** Add alongside, dual-write, remove old. Each sub-phase compiles and works independently.

---

## File Map

| File | Responsibility | N3.1 | N3.2 | N3.3 | N3.4 |
|------|---------------|------|------|------|------|
| `types/index.ts` | `GenerationRequest.params`, remove `GenerationSettings` | MODIFY | — | MODIFY | — |
| `hooks/use-generation.ts` | `filterSettingsForModel`, `initializeSettingsFromSchema` | MODIFY | — | — | — |
| `store/use-store.ts` | `modelSettings` + actions, model-switch save/load | — | MODIFY | MODIFY | — |
| `components/GenerationSettings.tsx` | Read from `modelSettings`, remove `generationSettings` ref | — | — | MODIFY | — |
| `components/GenerationSettingsFields.tsx` | Accept `Record<string, unknown>`, remove `VoiceGenerationDefaults` | — | — | MODIFY | — |
| `components/generation/GenerationPanel.tsx` | Use `filterSettingsForModel` on submit | — | — | — | MODIFY |

---

## N3.1 — Domain Migration (Types + Pure Functions)

**Files:** `types/index.ts`, `hooks/use-generation.ts`

**Strategy:** Add `params?: Record<string, unknown>` to `GenerationRequest` with JSDoc `@deprecated` on old fields. Add two exported pure functions. Zero behavioral change — old code paths untouched.

**Validation:** `filterSettingsForModel({num_step: 32, foo: "bar"}, schema)` → `{num_step: 32}`. `initializeSettingsFromSchema(schema)` → `{num_step: 32}`. TS clean.

- [ ] **1. Add `params` field to `GenerationRequest`** — add `params?: Record<string, unknown>` and `@deprecated` JSDoc on `num_step`, `guidance_scale`, `speed`, `duration`, `t_shift`, `denoise`

- [ ] **2. Add `filterSettingsForModel` export** — pure function in `hooks/use-generation.ts` that filters settings keys against `schema.properties`

- [ ] **3. Add `initializeSettingsFromSchema` export** — pure function in `hooks/use-generation.ts` that extracts defaults from schema properties

- [ ] **4. Run TypeScript check** — `npx tsc --noEmit`, expect 0 new errors (1 pre-existing)

- [ ] **5. Commit**
  ```
  feat(voice-first): add params field and model-scoped settings helpers (N3.1)
  ```

---

## N3.2 — Store Migration (Add modelSettings)

**Files:** `store/use-store.ts`

**Strategy:** Add `modelSettings: Record<string, Record<string, unknown>>` to store. Modify `setSelectedModelId` to save current settings to previous model's slot and load next model's saved settings. Add dual-write on `updateGenerationSettings`. `generationSettings` field still present — components continue to work. `GenerationSettings` container unchanged in this phase.

**Validation:** Switching models saves/restores settings per-model. Old `generationSettings` still accessible and dual-written. TS clean.

- [ ] **1. Add `modelSettings` field** — `modelSettings: Record<string, Record<string, unknown>>` initialized to `{}`

- [ ] **2. Modify `setSelectedModelId`** — save current `generationSettings` to `modelSettings[currentKey]`, load `modelSettings[nextKey]` or `defaultsToSettings(SYSTEM_DEFAULTS)` as new `generationSettings`

- [ ] **3. Add dual-write to `updateGenerationSettings`** — write to both `generationSettings` and `modelSettings[selectedModelId ?? "__default__"]`

- [ ] **4. Run TS check** — `npx tsc --noEmit`

- [ ] **5. Commit**
  ```
  feat(voice-first): add modelSettings store with per-model save/load (N3.2)
  ```

---

## N3.3 — Component Cleanup (Remove Old)

**Files:** `store/use-store.ts`, `components/GenerationSettings.tsx`, `components/GenerationSettingsFields.tsx`, `types/index.ts`

**Strategy:** Remove `generationSettings` and `GenerationSettings` type. Update `GenerationSettings` container to read from `modelSettings[selectedModelId]` directly. Update `GenerationSettingsFields` to accept `Record<string, unknown>` instead of `VoiceGenerationDefaults`. Maintain a hardcoded fallback schema for models without `settings_schema` so the UI doesn't break.

**Hardcoded fallback schema** — when `settingsSchema` is null, use a schema mapping the 6 OmniVoice params:
```typescript
const FALLBACK_SCHEMA: SettingsSchema = {
  type: "object",
  properties: {
    num_step: { type: "number", label: "Inference Steps", default: 32, minimum: 4, maximum: 64, step: 1 },
    guidance_scale: { type: "number", label: "Guidance Scale", default: 2.0, minimum: 0, maximum: 4, step: 0.1 },
    speed: { type: "number", label: "Speed", default: null, minimum: 0.5, maximum: 1.5, step: 0.05 },
    duration: { type: "number", label: "Duration (seconds)", default: null, minimum: 1, maximum: 120, step: 1 },
    t_shift: { type: "number", label: "Time Shift", default: 0.1, minimum: 0, maximum: 1, step: 0.01 },
    denoise: { type: "boolean", label: "Denoise", default: true },
  },
}
```

**Validation:** Generation settings render identical to before (both with and without model schema). No `generationSettings` or `GenerationSettings` references remain in the codebase. TS clean.

- [ ] **1. Remove `GenerationSettings` type** from `types/index.ts`

- [ ] **2. Add fallback schema constant** to `GenerationSettingsFields.tsx`

- [ ] **3. Update `GenerationSettingsFields`** — change `value` prop type from `VoiceGenerationDefaults` to `Record<string, unknown>`; change `onChange` type from `(next: VoiceGenerationDefaults) => void` to `(key: string, value: unknown) => void`; always render `DynamicSettingsForm` with the fallback schema or `settingsSchema`; remove hardcoded slider block; keep `use_gpu` switch as separate section below

- [ ] **4. Update `GenerationSettings` container** — read `modelSettings[selectedModelId]` instead of `generationSettings`; pass `Record<string, unknown>` to GenerationSettingsFields; update `handleFieldChange` to call `updateModelSetting` instead of `updateGenerationSettings`; remove `generationSettings` ref; remove `defaultsToSettings` call; keep `voiceDesign` and `useGpu` separate

- [ ] **5. Remove `generationSettings` and `updateGenerationSettings`** from store

- [ ] **6. Remove `defaultsToSettings` function** from store (no longer used)

- [ ] **7. Update `setSelectedProfile`** — stop setting `generationSettings`, use `activeVoiceDefaults` only for `voiceDesign` and `useGpu`; model settings load via `modelSettings` on model switch

- [ ] **8. Update `selectTemporaryVoice`** — same pattern, stop setting `generationSettings`

- [ ] **9. Update `discardTemporaryVoice`** — same pattern

- [ ] **10. Update `resetSettings`** — reset `modelSettings[selectedModelId]` to fallback defaults

- [ ] **11. Run TS check** — `npx tsc --noEmit`

- [ ] **12. Commit**
  ```
  feat(voice-first): remove legacy generationSettings, migrate to modelSettings (N3.3)
  ```

---

## N3.4 — Generation Pipeline (Filter Params)

**Files:** `components/generation/GenerationPanel.tsx`

**Strategy:** Update `handleGenerate` to call `filterSettingsForModel` before submission. Use the `params` field on `GenerationRequest`. Backend continues to work because it ignores unknown params.

**Validation:** Network request shows `params` object instead of individual fields. Unknown params are stripped. TS clean.

- [ ] **1. Import `filterSettingsForModel` and `useModels`** in GenerationPanel

- [ ] **2. Build `filteredParams` in `handleGenerate`**:
  ```typescript
  const currentModel = models?.find(m => m.id === selectedModelId)
  const filteredParams = filterSettingsForModel(
    { ...modelSettings },
    currentModel?.settings_schema
  )
  ```

- [ ] **3. Replace field spread with `params`** in mutation call:
  ```typescript
  generate.mutate({
    text: text.trim(),
    model_id: selectedModelId,
    voice_profile_id: voiceProfileId,
    language: language,
    ref_text: transcript || null,
    instruct: voiceDesign.length ? buildInstruct(voiceDesign) : null,
    params: filteredParams,
  })
  ```

- [ ] **4. Read `modelSettings` from store** instead of `generationSettings` (already removed)

- [ ] **5. Run TS check** — `npx tsc --noEmit`

- [ ] **6. Commit**
  ```
  feat(voice-first): filter generation params by model settings_schema (N3.4)
  ```

---

## N3.5 — Validation

**Files:** `STATUS.md`, `VALIDATION.md`

**Strategy:** Full TS check, lint check, update STATUS.md to mark N3 implemented, write validation summary.

- [ ] **1. Run `npx tsc --noEmit`** — confirm 0 new errors

- [ ] **2. Run `npx next lint`** — confirm clean

- [ ] **3. Update STATUS.md** — N3 → IMPLEMENTED, Implementation status → N1+N2+N3 IMPLEMENTED

- [ ] **4. Commit**
  ```
  chore(voice-first): validate and document N3 (N3.5)
  ```

---

## Self-Review Check

**Spec coverage:** TASKS.md §N3 — all 10 items covered across N3.1-3.4:
1. Replace `GenerationSettings` type → N3.1 (add) + N3.3 (remove)
2. Replace `GenerationRequest` fields with `params` → N3.1 (add field) + N3.4 (use it)
3. Replace `generationSettings` with `modelSettings` → N3.2 (add) + N3.3 (remove)
4. Add `initializeSettingsFromSchema` → N3.1 (add as pure fn)
5. Model switch logic → N3.2 (in `setSelectedModelId`)
6. Add `filterSettingsForModel` → N3.1 (add as pure fn) + N3.4 (wire)
7. Update GenerationPanel → N3.4
8. Update DynamicSettingsForm → already compatible (no change needed)
9. Update GenerationSettingsFields → N3.3
10. Migration in store init → N3.2 (dual-write, lazy migration)

**Placeholder scan:** All code blocks contain complete implementations.

**Type consistency:** `modelSettings` is `Record<string, Record<string, unknown>>` throughout. `filterSettingsForModel` and `initializeSettingsFromSchema` signatures match across all usages.

## Quick start

```bash
# Execute each sub-phase in order
git checkout feat/peakvox-phase-1
# ... implement N3.1 ...
# ... implement N3.2 ...
# ... implement N3.3 ...
# ... implement N3.4 ...
# ... implement N3.5 ...
```
