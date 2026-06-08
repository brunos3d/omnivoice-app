# OmniVoice Migration Audit (Task 10)

**Date:** 2026-06-08
**Subject:** Determine what is needed to migrate OmniVoice Base from in-process to a Runtime Service. DO NOT MIGRATE. Audit only.
**Status:** AUDIT COMPLETE
**Result:** OmniVoice migration is **deferred to Phase 6** per ADR-0017. Kokoro is the only runtime in Phase 3. The audit below documents the migration complexity for future planning.

---

## Current state (OmniVoice)

| Aspect | Value |
|---|---|
| Catalog id | `omnivoice-base` |
| Provider | `omnivoice` |
| Repo (legacy) | `k2-fsa/OmniVoice` (Hugging Face) |
| Model size | ~600M params (multilingual) |
| Capability | TTS (text-to-speech), multilingual (600+ languages) |
| Substrate | CPU + GPU |
| Edition | `ce`, `cloud` |
| Runtime descriptor | **None** (not in `runtime-registry/`) |
| Runtime service | **None** (no container, no FastAPI app, no Dockerfile) |
| Adapter | `OmniVoiceAdapter` (in-process; lazy-imports the framework) |
| Default model | `Settings.OMNIVOICE_MODEL = "k2-fsa/OmniVoice"` |
| GPU | `gpu: optional` (CPU works; GPU is much faster) |

The OmniVoice adapter is **in-process** — the model weights live in the backend image, the framework is imported lazily, and inference happens on the same host as the API. The user's "Model != Backend" invariant does NOT hold for OmniVoice today.

## What remains coupled to the backend

The audit identifies everything in the backend that knows about OmniVoice specifically (i.e. would have to change to migrate it to a Runtime Service).

### Hardcoded references (to be removed/migrated)

1. `backend/app/services/model_catalog.py:64-122` — `ModelDescriptor` for `omnivoice-base`.
2. `backend/app/services/model_catalog.py:153-205` — `ModelDescriptor` for `omnivoice-singing`.
3. `backend/app/services/model_wiring.py:21,44,78,82` — `BUILTIN_MODELS` referenced in `wire_registry_from_database` and `wire_runtime`.
4. `backend/app/core/migrations.py:19,105,186-202` — `_seed_builtin_models` seeds OmniVoice rows.
5. `backend/app/core/config.py:29` — `OMNIVOICE_MODEL = "k2-fsa/OmniVoice"` (the legacy in-process default).
6. `backend/app/services/model_providers/` — likely has an `OmniVoiceProvider` class.
7. `backend/app/services/runtime.py` — `OmniVoiceAdapter` (in-process) is registered with `PeakVoxRuntime`.
8. `backend/app/services/omnivoice_service.py` — likely a singleton service.
9. `backend/app/api/models.py:88-94` — `models_status_aggregate` returns `omnivoice_service.is_loaded`.
10. `frontend/src/types` — TypeScript `Model` type (includes OmniVoice fields).
11. `frontend/src/hooks/use-models.ts:115` — `useActiveModel` uses `m.is_default` to find the default; OmniVoice is likely the default.
12. `frontend/src/components/generation/` — components that may reference OmniVoice.

### Soft references (provider-agnostic; need verification)

The system has provider-agnostic abstractions (ADR-0003, ADR-0007, ADR-0008, ADR-0009). If those are respected, the migration to a runtime service should be a **descriptor change** + **adapter replacement**, not a refactor of the domain layer.

Verify:
- `ModelCapabilities` (the catalog capability surface) — no provider names.
- `ModelAdapter` Protocol — no provider names; the adapter's `generate(variant, artifact, text, params)` signature is provider-neutral.
- `HTTPTransport` (Phase 2C) — provider-neutral; the same transport works for Kokoro and OmniVoice.
- `KokoroAdapter` (the migrated adapter) — dispatches on `KOKORO_RUNTIME_URL`; the equivalent for OmniVoice would dispatch on a similar URL.

## Runtime service assets needed (the migration target)

Per R8, the migration target is a runtime-registry entry. The OmniVoice migration would create:

```
runtime-registry/omnivoice-base/
├── descriptor.json        (the contract; R2 build + R7 idle_timeout)
├── Dockerfile             (python:3.11-slim + omnivoice framework)
├── server.py              (FastAPI 5-endpoint contract)
├── requirements.txt       (omnivoice + torch + spacy)
├── README.md              (operator notes)
└── tests/                 (contract tests + Dockerfile structure tests)
```

The descriptor would look like (R8 mirror of Kokoro-82m):

```json
{
  "api_version": "peakvox.io/v1",
  "kind": "Runtime",
  "metadata": {
    "id": "omnivoice-base",
    "name": "OmniVoice Base Runtime",
    "description": "Runtime service for the OmniVoice 600M multilingual TTS model. CPU + CUDA-capable, 24kHz WAV output, 600+ languages.",
    "provider": "omnivoice",
    "version": "0.1.0",
    "edition": ["ce", "cloud"],
    "labels": { "substrate": "cpu+gpu", "model_family": "omnivoice" }
  },
  "spec": {
    "runtime_type": "docker",
    "image": {
      "repository": "peakvox/omnivoice-runtime",
      "tag": "0.1.0"
    },
    "build": {
      "entrypoint": "server.py",
      "build_context": ".",
      "dockerfile": "Dockerfile"
    },
    "service": {
      "protocol": "http",
      "port": 8000,
      "health_path": "/health",
      "readiness_path": "/ready",
      "generate_path": "/v1/generate",
      "build_path": "/v1/variants/build",
      "metadata_path": "/v1/metadata"
    },
    "capabilities": ["tts", "multilingual"],
    "requirements": {
      "gpu": "optional",
      "min_vram_gb": 4,
      "cpu_cores": 2,
      "memory_gb": 8,
      "edition": ["ce", "cloud"]
    },
    "model_binding": {
      "model_id": "omnivoice-base",
      "is_default": false,
      "priority": 200
    },
    "lifecycle": {
      "install_policy": "pull-on-install",
      "health_interval_seconds": 10,
      "health_timeout_seconds": 3,
      "start_timeout_seconds": 120,
      "restart_policy": "on-failure",
      "idle_timeout": "15m"
    }
  }
}
```

Differences from Kokoro:
- `provider: omnivoice` (not `kokoro`).
- `model_id: omnivoice-base` (catalog id).
- `is_default: false` (Kokoro is the default in Phase 3; OmniVoice becomes the default in Phase 6 if it becomes the primary runtime).
- `min_vram_gb: 4` (OmniVoice 600M is heavier than Kokoro 82M).
- `start_timeout_seconds: 120` (heavier model = longer load time).
- `edition: ["ce", "cloud"]` (OmniVoice is in both editions; Kokoro is CE-only in Phase 3).

The `server.py` would import OmniVoice's framework (whatever the package is) instead of `kokoro`. The 5-endpoint contract is identical.

## Runtime requirements

| Resource | Minimum | Recommended | Notes |
|---|---|---|---|
| CPU | 2 cores | 4+ cores | CPU is supported; GPU is much faster. |
| Memory | 8 GB | 16 GB | The model is ~2.4 GB on disk. |
| VRAM | 0 (CPU) | 4+ GB (GPU) | GPU strongly recommended for the multilingual model. |
| Disk | 4 GB | 8 GB | Model weights + cache. |
| Network | 1 Gbps | 1 Gbps | For HF download at install time. |

The image will be **larger** than Kokoro's (~3-5 GB vs ~1.5 GB) due to `torch` and the larger model. The CPU-only path is viable for development; the GPU path is needed for production.

## Image size expectations

Kokoro CPU: ~1.5 GB.
OmniVoice CPU: ~3-5 GB (torch + 600M model + spacy).
OmniVoice CUDA: ~5-7 GB (torch CUDA + 600M model).

For Phase 6, the OmniVoice runtime would be the **heaviest** runtime in the registry. The idle reaper (R7) is therefore important: a 4+ GB container held indefinitely is a significant resource cost.

## Migration complexity

**Estimated complexity:** moderate-to-high.

| Task | Effort | Notes |
|---|---|---|
| Author `runtime-registry/omnivoice-base/descriptor.json` | trivial | Copy Kokoro descriptor; change 6 fields. |
| Author `runtime-registry/omnivoice-base/server.py` | moderate | Implement the 5-endpoint contract on top of the OmniVoice framework. Requires understanding the OmniVoice framework's inference API. |
| Author `runtime-registry/omnivoice-base/requirements.txt` | trivial | Pin `torch` and OmniVoice framework version. |
| Author `runtime-registry/omnivoice-base/Dockerfile` | moderate | `python:3.11-slim` base; install torch + framework; copy server. |
| Author `runtime-registry/omnivoice-base/README.md` | trivial | Copy Kokoro README. |
| Author `runtime-registry/omnivoice-base/tests/` | moderate | Contract tests; gated E2E tests. |
| Update `BUILTIN_MODELS` to remove the in-process `omnivoice-base` (or keep as fallback) | trivial | TBD by the Phase 6 ADR. |
| Update `Settings` (`OMNIVOICE_MODEL`) | trivial | Keep the setting; the runtime service URL is the new data plane. |
| Replace `OmniVoiceAdapter` (in-process) with a runtime-aware adapter | moderate | Mirror `KokoroAdapter`: dispatch on `OMNIVOICE_RUNTIME_URL`. |
| Update the Models page to render the OmniVoice runtime card | trivial | The runtime-registry drives the UI (Task 3). |
| Update `docker-compose.yml` to add `peakvox-omnivoice-runtime` | trivial | Mirror Kokoro's compose entry. |
| **Total** | **~1-2 days of focused work** | Plus integration testing. |

## Blockers

1. **GPU availability in CI.** The CI lane is CPU-only. The CPU-only path of OmniVoice works but is slow. Real validation (G6-style E2E with audio) needs a GPU lane.
2. **OmniVoice framework access.** The `omnivoice-base` is `k2-fsa/OmniVoice` on Hugging Face. The packaging is non-trivial: it pulls in `transformers`, `torch`, and a custom inference script. The runtime container must build this reliably.
3. **The legacy in-process path is widely used.** Many tests assume the in-process adapter works. The migration must keep the in-process path as a fallback (mirroring Kokoro's CE default) until Phase 7 removes it.

## Phase sequencing (per ADR-0017)

| Phase | Provider | Status |
|---|---|---|
| Phase 3 | **Kokoro** (reference implementation) | IMPLEMENTED (P1-P5 + P8 done; P6, P7, P9 in progress). |
| Phase 4 | F5-TTS (second provider; the migration pattern is established). | NOT STARTED. |
| Phase 5 | Fish Audio S2 Pro (third provider; less common; tests the GPU-heavy path). | NOT STARTED. |
| Phase 6 | **OmniVoice Base** (the heavy multilingual provider; the hardest migration). | NOT STARTED. **This audit.** |
| Phase 7 | Remove direct in-process model execution. | NOT STARTED. The in-process path is the fallback until Phase 7 explicitly removes it. |

The migration sequence is intentional: **F5-TTS is the migration pattern** (a smaller, simpler model). Fish Audio tests the GPU path. OmniVoice is the heaviest migration and benefits from the patterns established by F5-TTS and Fish.

## What this audit recommends

1. **Do NOT migrate OmniVoice in Phase 3.** The user has explicitly directed this.
2. **Use the Kokoro reference shape** (`runtime-registry/kokoro-82m/`) as the template. The migration to `runtime-registry/omnivoice-base/` is a copy with 6 targeted edits to the descriptor plus the framework-specific source in `server.py`.
3. **Schedule Phase 6 in NEXT_TASK.md.** The migration is a focused 1-2 day effort, deferred to after F5-TTS (Phase 4) and Fish Audio (Phase 5) validate the migration pattern.
4. **Keep the in-process `OmniVoiceAdapter` as the fallback** until Phase 7 removes it. The runtime path is opt-in via `OMNIVOICE_RUNTIME_URL` (mirroring Kokoro's `KOKORO_RUNTIME_URL`).

---

**See also:**
[`docs/.agents/AUDITS/source-of-truth-audit.md`](source-of-truth-audit.md) (Task 1)
·
[`docs/.agents/AUDITS/models-page-integration-audit.md`](models-page-integration-audit.md) (Task 2)
·
[`docs/.agents/AUDITS/future-runtime-registry-standardization.md`](future-runtime-registry-standardization.md) (Task 11)
·
[`runtime-registry/kokoro-82m/`](../../../runtime-registry/kokoro-82m/) (R8 reference shape)
·
[`docs/.agents/SPECS/FEATURES/runtime-services-implementation/SPEC.md`](../SPECS/FEATURES/runtime-services-implementation/SPEC.md) (ADR-0017, Phase 4-6 sequencing)
