# Audits

Point-in-time audits of registry metadata, catalogs, and infrastructure against canonical
sources. The detailed audits live inside the Provider Validation program.

| Audit | Source | Finding (summary) |
|---|---|---|
| Model Registry / catalog metadata audit | [`../PROVIDER_VALIDATIONS/provider-validation.md`](../PROVIDER_VALIDATIONS/provider-validation.md) | Catalog structure reviewed; canonical metadata for Fish Audio S2 Pro, OmniVoice Base/Singing, Kokoro extracted and aligned to canonical sources; metadata gaps identified and corrected |
| Model installation infrastructure | [`../PROVIDER_VALIDATIONS/provider-validation.md`](../PROVIDER_VALIDATIONS/provider-validation.md) | HF installer `_KNOWN_PROVIDERS` limited to OmniVoice variants; Fish/Kokoro rejected by installer |
| Auto-routing readiness | [`../PROVIDER_VALIDATIONS/provider-validation.md`](../PROVIDER_VALIDATIONS/provider-validation.md) | `model="auto"` not implemented; metadata-readiness assessed |

These audits inform [`../../IMPLEMENTATION_STATUS.md`](../../IMPLEMENTATION_STATUS.md) and the
canonical-metadata decision (ADR-0007).

---

**Related:** [`../PROVIDER_VALIDATIONS/README.md`](../PROVIDER_VALIDATIONS/README.md) ·
[`../RESEARCH/README.md`](../RESEARCH/README.md)
