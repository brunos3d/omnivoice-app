# IMPLEMENTATION STATUS — the implementation lock file

> The authoritative map of what is actually built. **Documentation is not evidence;
> implementation requires code references.** This file is designed so it can eventually be
> partially regenerated from codebase analysis — every "IMPLEMENTED/VALIDATED" row cites
> concrete files and tests. Prefer code evidence over assumption; when in doubt, mark lower.

**Last verified against code:** 2026-06-05 (`feat/peakvox-phase-1`).
All paths are relative to repository root.

## Status vocabulary

| Status | Meaning |
|---|---|
| `NOT_STARTED` | No design, no code. |
| `PLANNED` | Roadmap/plan exists; no code. |
| `PROPOSED` | ADR/spec proposed, not accepted. |
| `APPROVED` | ADR accepted / spec approved; no implementation found. |
| `IN_PROGRESS` | Code being written now. |
| `PARTIAL` | Some code exists; not complete or not end-to-end proven. |
| `IMPLEMENTED` | Code complete; covered by automated tests. |
| `VALIDATED` | Implemented **and** proven end-to-end (for providers: real audio generated). |
| `SUPERSEDED` | Replaced by a later decision/implementation. |
| `DEPRECATED` | Retained but slated for removal. |
| `ARCHIVED` | Historical only. |

**Two distinct axes for providers:** *architecture* (can the platform represent/orchestrate
it — proven by contract tests) vs *provider* (does a real model run end-to-end — proven by
real inference). A row can be `IMPLEMENTED` on architecture and `PARTIAL`/`NOT_STARTED` on
provider validation.

---

## A. Architecture decisions (ADRs)

| ADR | Decision | Status | Implementation evidence |
|---|---|---|---|
| 0001 | Voice / VoiceVariant split | IMPLEMENTED | `backend/app/models/db.py` (`Voice`, `VoiceVariant`); `voice_variant_repository.py`; tests `test_voice_split_migration`, `test_voice_dual_write` |
| 0002 | Model as first-class entity | IMPLEMENTED | `model_registry.py`, `model_catalog.py`, `model_providers/`; `api/models.py`; tests `test_model_registry`, `test_model_catalog` |
| 0003 | Model Capability Contract | IMPLEMENTED | `models/registry_types.py::ModelCapabilities`, `services/capabilities.py`; tests `test_capabilities_contract`, `test_capabilities_service` |
| 0004 | Voice ≠ VoiceVariant ≠ Model separation | IMPLEMENTED | `services/model_adapter.py`, `runtime.py`; tests `test_runtime`, `test_universal_voice_asset` |
| 0005 | Edition-scoped model availability | IMPLEMENTED | `runtime.ensure_available`, `ModelDescriptor.editions`; tests `test_editions`, `test_model_availability`, `test_runtime_editions` |
| 0006 | Voice Variant Realization Types (open taxonomy) | IMPLEMENTED | `services/realization.py`; tests `test_realization`, `test_adapter_realization_surface` (status values superseded by 0008) |
| 0007 | Canonical Model Metadata Registry | IMPLEMENTED | `model_catalog.py`; tests `test_registry_metadata`, `test_models_api_metadata` |
| 0008 | Voice Variant Build Lifecycle (5-state) | IMPLEMENTED | `services/variant_lifecycle.py`; `runtime.build/rebuild/ensure_variant`; tests `test_variant_lifecycle`, `test_runtime_variant_lifecycle` (builds synchronous; async queue deferred) |
| 0009 | Artifact Versioning + Retention | IMPLEMENTED | `voice_variant_artifacts` table; `services/voice_variant_artifact_repository.py`; tests `test_artifact_versioning_migration`, `test_artifact_repository` |
| 0010 | Voice Source Assets + Automatic Variant Provisioning | IMPLEMENTED | `models/db.py::VoiceSourceAsset`, `core/migrations.py::_backfill_voice_source_assets`; backfill creates source-asset rows from variant artifacts. No dedicated provisioning service beyond `ensure_variant`. |
| 0011 | Voice Creation Sources | IMPLEMENTED | `creation_source` column on `Voice` model (`models/db.py`), migration backfill, generation dual-path uses `voice_id`. Full taxonomy + per-source provisioning policies (ADR-0012) not implemented. |
| 0016 | Models as Runtime Services | APPROVED | ADR accepted 2026-06-07. **No code in this phase** (architecture only). See `docs/.agents/SPECS/FEATURES/models-as-runtime-services/`. Introduces RuntimeRegistry, RuntimeManager, RuntimeDriver (with `DockerRuntimeDriver` as the first implementation); runtime infrastructure is *not* a domain concept. 7-phase migration: Phase 1 (this) → Phase 2 (Manager skeleton) → Phase 3 (Kokoro) → Phase 4 (F5-TTS reference) → Phase 5 (Fish) → Phase 6 (OmniVoice) → Phase 7 (remove in-process path). |
| 0017 | Runtime Services Implementation (Phase 2 Implementation ADR) | APPROVED | ADR accepted 2026-06-07. **No code in this phase** (architecture only). See `docs/.agents/SPECS/FEATURES/runtime-services-implementation/`. Specifies the 10 deliverables (RuntimeDescriptor schema, RuntimeRegistry model, RuntimeManager orchestration + resolution flows, RuntimeDriver Protocol + 8 error categories, DockerRuntimeDriver boundaries, Runtime Service Contract 5 endpoints, runtime routing 12-step flow, Kokoro migration 4-step rollout, CE/Cloud operations). Resolves the 5 deferred open questions from `OPEN_DECISIONS.md` Decision 10. Phase 2 sub-phases: 2A (foundations) → 2B (Docker driver) → 2C (Kokoro integration) → 2D (CE operations). Sub-phases begin after this accept. |

## B. Runtime components

| Component | Status | Evidence |
|---|---|---|
| `PeakVoxRuntime` single entry point | IMPLEMENTED | `services/runtime.py`; generation routes only through it; `test_runtime_wiring` |
| `ModelAdapter` contract | IMPLEMENTED | `services/model_adapter.py` |
| OmniVoice adapter | IMPLEMENTED (arch) / PARTIAL (provider) | `model_adapters/omnivoice_adapter.py` + `omnivoice_service.py` (real `from_pretrained`/`generate_async`); no automated end-to-end audio test |
| OmniVoice Singing adapter | PARTIAL | shares OmniVoice engine; catalog `status="disabled"`; unverified |
| Fish Audio adapter | PARTIAL (arch IMPLEMENTED, provider NOT_STARTED) | `model_adapters/fish_adapter.py` (HTTP client wired, real inference via S2 Pro server, unit-tested with mocks); real audio generation blocked — see Provider Validations |
| Kokoro adapter | IMPLEMENTED (arch) / PARTIAL (provider) | `model_adapters/kokoro_adapter.py` (82M, 54 presets, 9 languages, lazy `kokoro` import, WAV 24kHz); architecture-validated via mock-kokoro tests; real inference requires `kokoro` pip package. `build_variant()` creates metadata-only VoiceVariant (Phase 2) |
| `ProviderVoice` domain type + `ProviderVoiceRegistry` | IMPLEMENTED | `services/provider_voice.py` (frozen dataclass, O(1) dict lifecycle, search); tests `test_provider_voice` (31 tests) |
| `ProviderVoiceCatalog` protocol | IMPLEMENTED | `services/provider_voice.py` (`@runtime_checkable Protocol` on `ModelAdapter`); auto-populated at `register_adapter()` time |
| Variant resolution (`Voice+Model→Variant`) | IMPLEMENTED | `variant_resolution.py`; `test_variant_resolution`, `test_multimodel_resolution` |
| Capability validation / tag validation | IMPLEMENTED | `capabilities.py`, `tag_validation.py`, `tag_catalog.py` |
| Auto routing (`model="auto"`) | NOT_STARTED | metadata-readiness assessed only; no router |
| Async build queue | NOT_STARTED (deferred) | ADR-0008 Option 3; CE builds are synchronous |

### Phase 2A — Runtime Services Foundations (IMPLEMENTED 2026-06-07)

Phase 2A is **infrastructure foundation work** — no model is migrated, no
runtime is activated, no Docker integration is introduced. The driver is
not yet wired; in 2A the `RuntimeManager.resolve()` returns `None` and the
existing in-process path is taken unchanged. See
[`SPECS/FEATURES/runtime-services-implementation/TASKS.md` §2A](../SPECS/FEATURES/runtime-services-implementation/TASKS.md)
for the full task breakdown.

| Component | Status | Evidence |
|---|---|---|
| `RuntimeDescriptor` (Pydantic) | IMPLEMENTED | `app/services/runtime_types.py`; `tests/test_runtime_descriptor.py` (12 tests) — schema validation, DNS-label id, capability vocabulary, edition subset, sha256 digest, model_dump round-trip |
| `RuntimeInstance` (frozen dataclass) | IMPLEMENTED | `app/services/runtime_instance.py`; `tests/test_runtime_instance.py` (7 tests) — 7 RuntimeState values, 3 HealthState values, frozen ImageIdentity, equality |
| `HealthReport` / `Metrics` | IMPLEMENTED | `app/services/runtime_types.py`; `tests/test_runtime_health.py` (6 tests) — liveness/readiness enums, frozen report, empty Metrics |
| `RuntimeDriverError` hierarchy (8 subclasses) | IMPLEMENTED | `app/services/runtime_errors.py`; `tests/test_runtime_errors.py` (8 tests) — RuntimeNotFound, ImagePullError, SubstrateError, RuntimeAlreadyExists, RuntimeNotActive, TimeoutError, RuntimeRequirementsNotMet, RuntimeHealthFailed |
| `RuntimeDriver` Protocol (10 operations) | IMPLEMENTED | `app/services/runtime_driver.py`; `tests/test_runtime_driver_protocol.py` (3 tests) — `runtime_checkable`, structural conformance, rejects missing methods |
| `RuntimeRegistry` + `RuntimeRegistryLoader` | IMPLEMENTED | `app/services/runtime_registry.py`; `tests/test_runtime_registry.py` (10 tests) — indexes by id/model_id/capability, file walking, path-traversal guard, malformed-descriptor tolerance |
| `RuntimeEventBus` | IMPLEMENTED | `app/services/runtime_events.py`; `tests/test_runtime_events.py` (8 tests) — publish/subscribe, in-order dispatch, exception isolation, canonical event vocabulary (12 event types) |
| `RuntimeManager` skeleton | IMPLEMENTED | `app/services/runtime_manager.py`; `tests/test_runtime_manager.py` (11 tests) — orchestration only (no `generate`/`infer`/`load_weights` method), `resolve()` returns `None` in 2A, lifecycle operations raise `NoDriverConfigured` when no driver wired, event publication, in-process path preserved |
| PeakVoxRuntime bridge integration | IMPLEMENTED | `app/services/runtime.py` (`attach_runtime_manager` + bridge block in `generate`); `tests/test_runtime_routing_phase2.py` (10 tests) — transitional pass-through only; `Voice → VoiceVariant → Active Artifact → RuntimeManager (skeleton) → Adapter → existing inference path`; behavior unchanged in 2A; the 2C+ runtime-service branch is a documented-but-unreachable literal `pass` |

**Phase 2A architectural invariants (verified per the 2A gate checklist):**
- No `import docker` in `backend/app/services/runtime*.py` or `runtime.py`.
- No model framework imports (`torch`, `transformers`, `kokoro`, `f5_tts`, `fish_audio`) in runtime modules.
- No HTTP client imports (`requests`, `httpx`, `aiohttp`) in runtime modules.
- No runtime activation: `DockerRuntimeDriver` is introduced in sub-phase 2B.
- No Runtime Service communication: `HTTPTransport` is introduced in sub-phase 2C.
- No behavior regressions: full backend test suite (excluding pre-existing numpy/torch-dependent files) is 401 passed (was 374 before Phase 2 implementation began; +27 new tests for Phase 2A across 9 test files; all 52 pre-existing runtime tests continue to pass).

## C. Voice / data layer

| Subsystem | Status | Evidence |
|---|---|---|
| Voice identity (`public_voice_id`) | IMPLEMENTED | `models/db.py::Voice`; `voice_repository.py` |
| VoiceVariant realization | IMPLEMENTED | `models/db.py::VoiceVariant`; `voice_variant_repository.py` |
| VoiceVariantArtifact versioning | IMPLEMENTED | `voice_variant_artifact_repository.py` |
| Voice onboarding pipeline | IMPLEMENTED | `voice_onboarding.py`, `audio_preprocessing_service.py` |
| Voice Source Asset layer | PARTIAL | schema/UI references present; full ADR-0010 provisioning not built |
| ProviderVoice (ephemeral preset voices) | IMPLEMENTED | `services/provider_voice.py` (no DB, no assets, no variants, no provisioning — ADR-0010 §8 exempt); catalog-only since Phase 2 — two-tier resolution removed from `runtime.generate()` |
| Idempotent SQLite migrations | IMPLEMENTED | `core/migrations.py` |
| Storage abstraction | IMPLEMENTED | `services/storage.py` |

## D. API layer

| Surface | Status | Evidence |
|---|---|---|
| Versioned `/api/v1` | IMPLEMENTED (harden pending P9) | `api/v1.py` |
| `/voices` CRUD | IMPLEMENTED | `api/voices.py` |
| `/variants` (+ summary, backfill) | IMPLEMENTED | `api/variants.py`, `api/variants_summary.py` |
| `/models` (+ lifecycle) | IMPLEMENTED | `api/models.py` |
| `/generate` + jobs | IMPLEMENTED | `api/generation.py` |
| `GET /api/provider-voices` | IMPLEMENTED | `api/provider_voices.py`; tests `test_provider_voices_api` (7 tests) |
| `POST /voices/from-preset` | IMPLEMENTED | `api/voices.py` (create_voice_from_preset); tests `test_voices_from_preset` (2 tests) |
| Hashed API keys | IMPLEMENTED | `api/api_keys.py`, `services/api_keys.py` |
| `/v1/speech/generate` final contract freeze | PLANNED (P9) | — |

## E. Frontend

| Surface | Status | Evidence |
|---|---|---|
| Voice Library 2.0 (tabs, source asset, variants, artifacts) | IMPLEMENTED | `frontend/src/components/voice/*` |
| Preset Voices tab | IMPLEMENTED | `frontend/src/components/voice/PresetVoicesTab.tsx`; registered in `voices/page.tsx` |
| Variant Dashboard + backfill UX | IMPLEMENTED | `VariantDashboard.tsx`, `ModelCompatibilitySection.tsx` |
| Capability-driven generation controls | IMPLEMENTED | `GenerationPanel` (Voice Design gating) |
| Commercial nav (marketplace/creator/billing) | NOT_STARTED (flag-gated, hidden in CE) | — |

## F. Cloud / commercial (schema-ready only)

| Subsystem | Status | Evidence |
|---|---|---|
| Auth (Clerk adapter, principal resolution, roles) | APPROVED / NOT_STARTED | `AuthProvider` seam only |
| Billing (credits, metering, Stripe) | APPROVED / NOT_STARTED | empty tables + `BillingProvider`/`PaymentProvider` seams |
| Creators (profiles, Connect, royalties) | APPROVED / NOT_STARTED | empty `creators` table |
| Marketplace (listings, discovery, royalty-on-use) | APPROVED / NOT_STARTED | empty `marketplace_listings` table |
| Cloud infra (Postgres, Alembic, workers, CDN) | PLANNED | — |
| Production scaling | PLANNED | — |

---

## How to update this file

1. Verify against code, not memory or docs. Open the cited files.
2. Add or adjust the `Evidence` column with concrete `path` + `test_name` references.
3. Downgrade status the moment evidence is missing. An ADR being Accepted is `APPROVED`, not
   `IMPLEMENTED`.
4. Distinguish architecture-validated from provider-validated for anything touching a model.
5. Update [`PROJECT_STATE.md`](PROJECT_STATE.md) and [`HANDOFF.md`](HANDOFF.md) in the same change.

**Related:** [`DECISIONS/ADR_INDEX.md`](DECISIONS/ADR_INDEX.md) ·
[`VALIDATION/RETROSPECTIVES/`](VALIDATION/RETROSPECTIVES/) ·
[`IMPLEMENTATION/EXECUTION_HISTORY/EXECUTION_LEDGER.md`](IMPLEMENTATION/EXECUTION_HISTORY/EXECUTION_LEDGER.md)
