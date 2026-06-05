# Feature Specs

Each future feature gets its own folder here:

```
FEATURES/<feature-name>/
  SPEC.md         # what & why (problem, requirements, acceptance criteria)
  DESIGN.md       # how (components, data, runtime impact, constrained ADRs)
  TASKS.md        # task-by-task breakdown (TDD)
  VALIDATION.md   # how it's proven (tests; architecture vs provider)
  STATUS.md       # lifecycle position + outcome
```

Copy from [`../TEMPLATES/`](../TEMPLATES/) to start.

## Existing design specs (canonical, pre-this-KB)

These live under [`.`](.) and predate the
per-feature folder convention:

| Spec | File |
|---|---|
| Voice Library 2.0 | [`2026-06-04-voice-library-2-design.md`](2026-06-04-voice-library-2-design.md) |
| PeakVox Runtime Validation | [`2026-06-04-peakvox-runtime-validation-design.md`](2026-06-04-peakvox-runtime-validation-design.md) |
| Voice Entity Foundation | [`2026-06-03-voice-entity-foundation-design.md`](2026-06-03-voice-entity-foundation-design.md) |
| Voice Library Redesign | [`2026-06-03-voice-library-redesign-design.md`](2026-06-03-voice-library-redesign-design.md) |
| SaaS Architecture | [`2026-06-03-saas-architecture-design.md`](2026-06-03-saas-architecture-design.md) |
| Language Registry | [`2026-06-03-language-registry-design.md`](2026-06-03-language-registry-design.md) |
| TTS Auto-Config | [`2026-06-03-tts-auto-config-design.md`](2026-06-03-tts-auto-config-design.md) |
| Dev Profile | [`2026-06-03-dev-profile-design.md`](2026-06-03-dev-profile-design.md) |
| OmniVoice Redesign | [`2026-06-02-omnivoice-redesign-design.md`](2026-06-02-omnivoice-redesign-design.md) |

New features should adopt the folder convention above.
