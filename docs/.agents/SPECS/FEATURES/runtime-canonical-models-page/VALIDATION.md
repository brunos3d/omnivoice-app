# VALIDATION — Runtime-Canonical Models Page

> **Companion to:** [`SPEC.md`](./SPEC.md) · [`DESIGN.md`](./DESIGN.md) ·
> [`TASKS.md`](./TASKS.md)
> **Date:** 2026-06-08

This document is filled in after implementation completes. See
TASKS §T6–T9 for the evidence required.

---

## Pre-conditions verified

- [x] T0: backend coverage confirmed
  (`/api/models/with-runtimes` returns 4 catalog models,
  Kokoro with 1 runtime, the other 3 with empty `runtimes[]`)
- [x] T6: `tsc --noEmit` passes (0 errors)
- [x] T6: `eslint src/app/models src/components/models` passes
  (0 errors, 0 warnings)
- [x] T6: backend logs clean during page load
- [x] T6: `docker compose ps` shows 3 services healthy
  (`backend`, `minio`, `kokoro-runtime`)
- [x] T6: API responses unchanged after refactor —
  `/api/models/with-runtimes` returns the same 4 cards,
  `/api/runtimes` returns 1 entry, `/api/runtimes/kokoro-82m/state`
  returns `phase: NotInstalled`

## Behavior verification

- [x] T7: `Kokoro 82M` right panel shows the full Runtime section
      (image `peakvox/kokoro-runtime:0.1.0`, runtime name
      `Kokoro 82M Runtime`, SERVICE block with all 5 paths,
      REQUIREMENTS block with GPU/Min VRAM/CPU/Memory/Edition,
      CAPABILITIES chip `tts`, single `[Install]` operations button)
- [x] T7: `OmniVoice Base` right panel shows
      `Runtime Not Migrated` with phase hint `Phase 6 — OmniVoice migration`
- [x] T7: `OmniVoice Singing + Emotion` shows `Runtime Not Migrated`
- [x] T7: `Fish Audio S2 Pro` shows `Runtime Not Migrated` with
      `Deferred — hardware blocker (codec/VRAM)`
- [x] T7: only one `GET /models/with-runtimes` fires on initial
      load (no legacy `GET /models` call)
- [x] T7: no legacy `Lifecycle` block in the rendered DOM
- [x] T7: 0 console errors, 0 console warnings in Chrome DevTools

## Screenshots

- [x] `audits/screenshots/omnivoice-base-not-migrated.png`
- [x] `audits/screenshots/kokoro-runtime-section.png`
- [x] `audits/screenshots/fish-s2-pro-not-migrated.png`

## Behavior changes (acknowledged)

- The legacy Activate / Deactivate buttons are removed. The
  runtime's `Active` phase is the new "activated" state. This is
  the intended architectural change; documented here so the change
  is traceable.
- The `useModels()` (legacy catalog) call is removed from the
  Models page. The page now depends solely on
  `useModelsWithRuntimes()`. The terminal check (T0) confirmed
  the backend returns the catalog model in the composed view
  even when `runtimes[]` is empty.

## Audit report

See
[`audits/models-page-canonical-control-surface.md`](./audits/models-page-canonical-control-surface.md)
for the full narrative audit with before/after screenshots.
