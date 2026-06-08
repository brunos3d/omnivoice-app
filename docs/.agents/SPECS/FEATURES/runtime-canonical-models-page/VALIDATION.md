# VALIDATION — Runtime-Canonical Models Page

> **Companion to:** [`SPEC.md`](./SPEC.md) · [`DESIGN.md`](./DESIGN.md) ·
> [`TASKS.md`](./TASKS.md)
> **Date:** 2026-06-08

This document is filled in after implementation completes. See
TASKS §T6–T9 for the evidence required.

---

## Pre-conditions verified

- [ ] T0: backend coverage confirmed
  (`/api/v1/models/with-runtimes` returns catalog + runtimes)
- [ ] T6: `npm run typecheck` passes
- [ ] T6: `npm run lint` passes
- [ ] T6: backend logs clean during page load
- [ ] T6: `docker compose ps` shows all services healthy

## Behavior verification

- [ ] T7: `Kokoro 82M` right panel shows the full Runtime section
      (image, repository, tag, port, endpoint, state, capabilities,
      requirements, single operations surface)
- [ ] T7: `OmniVoice Base` right panel shows the
      `Runtime Not Migrated` empty state with the correct phase hint
- [ ] T7: `OmniVoice Singing + Emotion` shows `Runtime Not Migrated`
- [ ] T7: `Fish Audio S2 Pro` shows `Runtime Not Migrated`
- [ ] T7: only one `GET /api/v1/models/with-runtimes` fires on
      initial load
- [ ] T7: when `Kokoro 82M` is selected,
      `GET /api/v1/runtimes/kokoro-82m/state` polls at ~10s
- [ ] T7: no legacy `Lifecycle` block in the rendered DOM

## Screenshots

- [ ] `audits/screenshots/kokoro-82m-runtime-section.png`
- [ ] `audits/screenshots/omnivoice-base-not-migrated.png`
- [ ] `audits/screenshots/fish-s2-pro-not-migrated.png`

## Behavior changes (acknowledged)

- The legacy Activate / Deactivate buttons are removed. The
  runtime's `Active` phase is the new "activated" state. This is
  the intended architectural change; documented here so the change
  is traceable.

## Audit report

See
[`audits/models-page-canonical-control-surface.md`](./audits/models-page-canonical-control-surface.md)
for the full narrative audit with before/after screenshots.
