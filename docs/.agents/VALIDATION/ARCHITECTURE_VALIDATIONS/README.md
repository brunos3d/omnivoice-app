# Architecture Validations

Evidence that the platform can **represent and orchestrate** its concepts — proven by automated
tests over the contracts and data model (not by real model inference; that is
[`../PROVIDER_VALIDATIONS/README.md`](../PROVIDER_VALIDATIONS/README.md)).

**Test baseline:** ~237+ backend tests across 57 test files (`backend/tests/`).

## What is architecture-validated (with representative tests)

| Capability | Representative tests |
|---|---|
| Voice identity (stable `public_voice_id`) | `test_voice_split_migration`, `test_universal_voice_asset` |
| VoiceVariant resolution | `test_variant_resolution`, `test_runtime` |
| Runtime orchestration (single entry point, no bypass) | `test_runtime`, `test_runtime_wiring` |
| Model registry + canonical metadata | `test_model_registry`, `test_registry_metadata`, `test_models_api_metadata` |
| Capability contract (declared, not inferred) | `test_capabilities_contract`, `test_capabilities_service`, `test_catalog_capabilities` |
| Realization-type taxonomy (open) | `test_realization`, `test_adapter_realization_surface` |
| Variant build lifecycle (5-state) | `test_variant_lifecycle`, `test_runtime_variant_lifecycle` |
| Artifact versioning + rollback + retention | `test_artifact_repository`, `test_artifact_versioning_migration` |
| Edition availability | `test_editions`, `test_model_availability`, `test_runtime_editions` |
| Multi-provider resolution (3 adapters) | `test_multimodel_resolution`, `test_universal_voice_asset` |
| Variants API | `test_variants_api` |

## Boundary (what these tests do NOT do)

They do not load real weights, use a GPU, or synthesize audio — by design (CI has no GPU and
must not download multi-GB weights). That is exactly why provider validation is a separate,
mostly-open program.

---

**Related:** [`../../IMPLEMENTATION_STATUS.md`](../../IMPLEMENTATION_STATUS.md) ·
[`../RETROSPECTIVES/README.md`](../RETROSPECTIVES/README.md)
