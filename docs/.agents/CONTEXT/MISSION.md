# Mission

Make voice a **portable, ownable, model-independent asset**, and make every speech model
reachable through **one stable runtime and one stable API**.

## What we are building

1. **A universal runtime** that joins `Voice + Model → VoiceVariant → speech`, absorbing model
   diversity behind the `ModelAdapter` seam.
2. **A self-hostable infrastructure layer (CE)** that is genuinely useful on its own: local
   models, voice library, generation.
3. **An ecosystem layer (Cloud)** — marketplace, creators, royalties, billing, multi-tenant
   auth — schema-ready in CE, enabled in Cloud, never a forked schema.

## What success looks like

- A developer integrates **once** and can switch models without code changes.
- A voice creator publishes **once**; the same `public_voice_id` works across every provider.
- Adding a new model is **wiring, not redesign** — no public API, Voice ID, or integration
  changes.
- The platform can honestly state which providers are *architecture-validated* vs
  *provider-validated*.

## Editions

| | Community Edition (CE) | PeakVox Cloud |
|---|---|---|
| Role | Infrastructure layer | Ecosystem layer |
| Hosting | Self-hosted (Docker) | Managed, multi-tenant |
| Marketplace / creators / billing / auth | Schema-ready, disabled | Enabled |

---

**Related:** [`VISION.md`](VISION.md) · [`PRODUCT_PRINCIPLES.md`](PRODUCT_PRINCIPLES.md) ·
[`ECOSYSTEM.md`](ECOSYSTEM.md) · [`../ARCHITECTURE/product-architecture.md`](../ARCHITECTURE/product-architecture.md)
