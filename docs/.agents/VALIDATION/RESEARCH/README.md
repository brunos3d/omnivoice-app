# Research

Provider and capability research that informs decisions but is not yet a validated provider.

| Topic | Source | Status |
|---|---|---|
| Kokoro-82M (preset voice packs, non-cloning) | [`../PROVIDER_VALIDATIONS/provider-validation.md`](../PROVIDER_VALIDATIONS/provider-validation.md) §Kokoro | Research-only — no adapter, no catalog entry |
| Fish Audio S2 Pro canonical metadata | [`../PROVIDER_VALIDATIONS/provider-validation.md`](../PROVIDER_VALIDATIONS/provider-validation.md) | Extracted; adapter built; inference blocked |
| Language registry | [`../../SPECS/FEATURES/2026-06-03-language-registry-design.md`](../../SPECS/FEATURES/2026-06-03-language-registry-design.md) · [`../../../LANGUAGES.md`](../../ARCHIVE/LEGACY/LANGUAGES.md) | Design |
| TTS auto-config | [`../../SPECS/FEATURES/2026-06-03-tts-auto-config-design.md`](../../SPECS/FEATURES/2026-06-03-tts-auto-config-design.md) | Design |

## Why Kokoro matters

Kokoro is the **stress test** for the Universal Voice Runtime thesis: it has fixed preset voice
packs and **cannot clone a voice from reference audio**. This challenges ADR-0008's assumption
that a variant is *built from the Voice's reference audio*, and is the empirical proof point the
architecture still needs. It motivates reserved ADR-0012 (provisioning policies) and ADR-0013
(model categories).

---

**Related:** [`../PROVIDER_VALIDATIONS/README.md`](../PROVIDER_VALIDATIONS/README.md) ·
[`../../DECISIONS/ADR_INDEX.md`](../../DECISIONS/ADR_INDEX.md) (reserved ADRs)
