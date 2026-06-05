# Ecosystem

How PeakVox positions itself and how its pieces relate. Canonical detail in
[`../ARCHITECTURE/overview.md`](../ARCHITECTURE/overview.md),
[`../ARCHITECTURE/marketplace-architecture.md`](../ARCHITECTURE/marketplace-architecture.md),
[`../ARCHITECTURE/cloud-architecture.md`](../ARCHITECTURE/cloud-architecture.md),
[`../ARCHITECTURE/monetization-architecture.md`](../ARCHITECTURE/monetization-architecture.md).

## Analogy

PeakVox is to voice what a combination of these is to text/audio:

- **OpenRouter** — model-agnostic routing through one API.
- **Hugging Face** — a model + asset registry.
- **Ollama / LM Studio** — effortless local self-hosted runtime + model lifecycle.
- **ElevenLabs** — voice products + a creator economy.

## The two layers

```
                 ┌─────────────────────────────────────────────┐
   Ecosystem     │  PeakVox Cloud                              │
   (Cloud-only)  │  marketplace · creators · royalties ·       │
                 │  credits · payouts · multi-tenant auth      │
                 └─────────────────────────────────────────────┘
                                    ▲  schema-ready in CE, enabled in Cloud
                 ┌─────────────────────────────────────────────┐
   Infrastructure│  Community Edition (CE)                      │
   (self-hosted) │  Universal Voice Runtime · model registry · │
                 │  voice library · generation · public API    │
                 └─────────────────────────────────────────────┘
```

**Open-core boundary:** marketplace, creators, royalties, credits, transactions, payouts, and
multi-tenant auth are Cloud-only. Their domain models, tables, and API boundaries exist in CE
from day one, disabled behind feature flags and deployment boundaries — so Cloud is wiring, not
a domain redesign.

## Actors

- **Self-hoster / owner** (CE) — runs the runtime locally, manages models and voices.
- **Developer** — integrates `voice + model + text` once.
- **Voice creator** (Cloud) — owns voices, earns royalties.
- **Consumer** (Cloud) — discovers and uses marketplace voices.

---

**Related:** [`MISSION.md`](MISSION.md) · [`../ROADMAP/ROADMAP.md`](../ROADMAP/ROADMAP.md)
