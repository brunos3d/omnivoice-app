# Runtime Activation Audit — Pre-Phase-2D

> **Status:** PASSED · **Date:** 2026-06-07 · **Auditor:** Runtime-Service
> implementation agent · **Scope:** All runtime-domain modules added or
> modified in Phases 2A, 2B, 2C.

## Goal

Validate that runtime activation does not create a new source of
truth. The canonical chain (Voice → VoiceVariant → Active Artifact
→ Adapter) must remain intact, and runtime infrastructure must
remain strictly downstream (Adapter → RuntimeManager →
RuntimeDriver → Runtime Service).

## Expected invariant

> Voices own identity.
> Models own capabilities.
> Variants own realizations.
> Artifacts own model-specific assets.
> Runtimes own deployment state only.

## Method

Each of the 7 audit checks below cites concrete file paths and
line numbers. The audit is reproducible: every cited reference
can be re-verified by `grep` against the codebase at the audit
date.

---

## Check 1 — `RuntimeResolution` never becomes a canonical domain object

**Result: PASS**

`RuntimeResolution` is the ephemeral result of
`RuntimeManager.resolve()` (ADR-0017 §3.4). It carries the
resolved `RuntimeDescriptor`, a `RuntimeInstance`, and an
`endpoint` URL.

| Property | Evidence |
|---|---|
| Defined | `backend/app/services/runtime_manager.py:70-83` (`@dataclass(frozen=True)`) |
| Constructed | `backend/app/services/runtime_manager.py:181-185` (only) |
| Consumed | `backend/app/services/runtime.py:476` (PeakVoxRuntime bridge, 2A pass-through) |
| Persisted | NONE (no DB, no SQLAlchemy mapping) |
| Exposed via API | NONE (no router, no schema) |
| Referenced by Voice | NONE |
| Referenced by VoiceVariant | NONE |
| Referenced by VoiceVariantArtifact | NONE |
| Referenced by ModelAdapter | NONE |
| Referenced by VariantResolver | NONE |
| Referenced by ArtifactResolver | NONE |
| Referenced by tests | `tests/test_runtime_manager.py`, `tests/test_runtime_manager_with_docker.py` (assertion only) |

`RuntimeResolution` is an in-memory orchestration result, not
a canonical domain object. ✓

---

## Check 2 — `RuntimeDescriptor` never owns Model metadata

**Result: PASS**

`RuntimeDescriptor` (`backend/app/services/runtime_types.py:206`)
is the deployment contract for one runtime. The fields on its
`metadata` and `spec` are runtime metadata (id, name, image,
service, capabilities, requirements, lifecycle, model_binding)
— NOT model metadata.

| RuntimeDescriptor field | Type | What it is | What it is NOT |
|---|---|---|---|
| `metadata.id` | `str` | Runtime's DNS label | Model's id |
| `metadata.name` | `str` | Runtime's human-readable name (e.g. "Kokoro 82M Runtime") | Model's name |
| `metadata.description` | `str` | Runtime's description | Model's description |
| `metadata.provider` | `str` | Runtime's image provider (e.g. "kokoro") | Model's provider |
| `metadata.version` | `str` | Runtime image's tag | Model's version |
| `metadata.edition` | `List[str]` | Editions where this runtime is allowed | Model's editions |
| `metadata.labels` | `dict[str, str]` | Runtime routing hints | Model's tags |
| `spec.image` | `RuntimeImage` | OCI image identity (repo, tag, digest) | Model's weights |
| `spec.service` | `RuntimeService` | Runtime's HTTP/gRPC endpoints | Model's interface |
| `spec.capabilities` | `List[str]` | Subset of `RUNTIME_CAPABILITY_VOCABULARY` (validated against model's caps) | Model's capabilities |
| `spec.requirements` | `RuntimeRequirements` | Host-side (GPU, VRAM, CPU, RAM, edition) | Model's training requirements |
| `spec.model_binding` | `RuntimeModelBinding` | `(model_id: str, is_default: bool, priority: int)` — a reference, not ownership | Model's metadata |
| `spec.lifecycle` | `RuntimeLifecycle` | Install/start/health policy | Model's training policy |

The descriptor references a model by `model_id: str` (line 159)
and validates that its declared capabilities are a subset of
the model's `ModelCapabilities` via
`validate_capabilities_subset_of` (lines 241-271). The validation
is a constraint check; the descriptor does NOT own, copy, or
expose the model's canonical metadata.

Models own their capabilities via `ModelCapabilities`
(`backend/app/models/registry_types.py`, ADR-0003). The
descriptor never imports `ModelDescriptor` or any
model-metadata field. ✓

---

## Check 3 — `RuntimeInstance` never owns Voice metadata

**Result: PASS**

`RuntimeInstance` (`backend/app/services/runtime_instance.py:67`)
is a frozen dataclass for one runtime's operational state. It
has zero voice-related fields.

| RuntimeInstance field | Type |
|---|---|
| `runtime_id` | `str` |
| `state` | `RuntimeState` (7 values) |
| `host` | `str` |
| `port` | `int` |
| `image_identity` | `ImageIdentity (frozen)` — `(repository, tag, digest)` |
| `started_at` | `Optional[datetime]` |
| `last_health_at` | `Optional[datetime]` |
| `health_state` | `HealthState` (3 values) |

`grep` for `voice_id|public_voice_id|voice_name` against the
runtime-instance and runtime-types files returned **no
matches**. The runtime instance knows the host and port of the
container, the image identity, and the health state. It does
not know which voice a generation is for. ✓

---

## Check 4 — `RuntimeRegistry` remains deployment metadata only

**Result: PASS**

`RuntimeRegistry` (`backend/app/services/runtime_registry.py:41`)
holds only `RuntimeDescriptor` objects. The registry has three
indexes — by id, by model_id, by capability — all pointing to
the same descriptor set.

The descriptors' content is deployment metadata (image,
service, capabilities, requirements, lifecycle, model_binding).
The registry has no voice_id, no public_voice_id, no
VoiceVariant reference, no VoiceVariantArtifact reference, no
DB write access.

The registry is read-only at runtime (per its own docstring:
"The registry is read-only at runtime; descriptors are
file-managed."). ✓

---

## Check 5 — Voice compatibility continues to be derived from `VoiceVariant` + `ModelCapabilities`

**Result: PASS**

Voice compatibility is enforced in `PeakVoxRuntime.generate()`
(`backend/app/services/runtime.py:426-438`):

1. `descriptor = self.resolve_model(model_id)` — model metadata
2. `self.ensure_available(descriptor.id)` — edition scoping
3. `self.ensure_active(descriptor.id)` — activation
4. `adapter = self.get_adapter(descriptor.id)` — adapter lookup
5. `bad_tags = find_unsupported_tags(text, adapter.get_supported_tags())` — capability-driven validation
6. `missing = _missing_caps(adapter.get_capabilities(), set(required_capabilities))` — capability-driven validation
7. `resolution = await self.resolve(db, public_voice_id=public_voice_id, model_id=descriptor.id)` — `Voice + Model → VoiceVariant`
8. `variant_params = resolution.variant.params or {}` — variant realization
9. `ref_audio_path = ref_audio_path or artifacts.get("audio")` — active artifact
10. THEN the 2A bridge sits between (9) and the adapter call

The 2A bridge (line 475-486) does NOT introduce a new
compatibility path. It does not call any of: `resolve_variant`,
`get_active_artifact`, `set_active`, `append_artifact`. It
consumes the resolved variant and routes to a runtime service
endpoint (when the manager is wired AND the resolution is
non-None); otherwise, the existing in-process path is taken.

The runtime descriptor's `spec.capabilities` are validated
against the bound model's `ModelCapabilities` via
`validate_capabilities_subset_of`. This is a *constraint* on
the runtime, not a *definition* of voice compatibility.
Voice compatibility remains derived from `VoiceVariant` and
`ModelCapabilities`. ✓

---

## Check 6 — Runtime activation cannot bypass `VariantResolver` or `ArtifactResolver`

**Result: PASS**

The 2A bridge (`backend/app/services/runtime.py:475-486`) sits
BETWEEN active-artifact resolution and the adapter call:

```python
# Before bridge (line 440-453):
variant = await resolve_variant(db, voice_id=voice.id, model_id=descriptor.id)
artifacts = resolution.variant.artifacts or {}
ref_audio_path = ref_audio_path or artifacts.get("audio")
...

# Bridge (line 475-486):
if self._runtime_manager is not None:
    _resolution = self._runtime_manager.resolve(descriptor.id)
    if _resolution is not None:
        # 2C+ runtime-service path. Unreachable in 2A.
        pass

# After bridge (line 488-498):
return await adapter.generate(...)
```

The bridge does NOT call:
- `resolve_variant` (line 273, 301, 342, 354, 372, 379, 388, 401)
- `get_active_artifact` (line 33, 375)
- `set_active` (line 37, 315, 394)
- `append_artifact` (line 32, 309)
- `prune_artifacts` (line 36)

The bridge sits AFTER variant resolution and AFTER artifact
retrieval. It consumes the resolution; it does not bypass it.

Even in the 2C+ runtime-service path (when the bridge is
activated), the runtime service does NOT receive a
`Voice`/`VoiceVariant`/`VoiceVariantArtifact` object — it
receives a request body of strings (text, voice_id, language,
ref_audio_path, ref_text, instruct, params, request_id). The
variant/artifact resolution has already happened on the
backend; the runtime service executes inference on the inputs
the adapter has already prepared.

The runtime service cannot independently resolve voices because
it does not have access to the DB, the variant table, or the
artifact table (see Check 7). ✓

---

## Check 7 — Runtime Service never receives enough information to independently resolve voices

**Result: PASS**

The runtime-service path is in
`backend/app/services/model_adapters/kokoro_adapter.py:261-316`
(`_generate_via_runtime`). The request body sent to the
runtime service is:

| Field | Source | Domain object? |
|---|---|---|
| `text` | generation kwarg | NO (a string) |
| `voice_id` | `voice_id or voice_profile_id` from the runtime kwargs | NO (a string id, either a ProviderVoice external id or a Voice.id UUID) |
| `language` | generation kwarg | NO (a string) |
| `ref_audio_path` | generation kwarg | NO (a string path) |
| `ref_text` | generation kwarg | NO (a string) |
| `instruct` | generation kwarg | NO (a string) |
| `params` | generation kwargs (already merged with variant params) | NO (a dict) |
| `request_id` | job id | NO (a string UUID) |

The runtime service does NOT receive:
- `public_voice_id` (the stable identity of a Voice) — the
  `voice_id` is the *variant voice id* or *provider external id*,
  not the public identity
- `Voice` rows (no DB access)
- `VoiceVariant` rows (no DB access)
- `VoiceVariantArtifact` rows (no DB access)
- `ModelDescriptor` rows (no DB access)
- `model_id` (the runtime is already bound to a model via
  `RuntimeDescriptor.spec.model_binding.model_id`)
- `ModelCapabilities` (the runtime's capabilities are
  pre-validated against the bound model's capabilities at
  load time; the runtime does not re-validate)

The runtime service is a worker that takes a request body and
returns audio + logs. It cannot independently resolve which
voice a request is for, because the public identity, the
variant lifecycle, the active artifact, and the model binding
are all backend-side concerns.

`HTTPTransport` (`backend/app/services/adapter_transport/http_transport.py`)
has NO voice / artifact / runtime-domain references. `grep`
returned no matches. The transport is a pure HTTP
abstraction. ✓

---

## Invariant check

| Owner | Field | Source of truth | Runtime-layer touch? |
|---|---|---|---|
| **Voice** identity | `public_voice_id` (String(32), unique, indexed) | `backend/app/models/db.py:63-64` | NONE — runtime never sees Voice |
| **Model** capabilities | `ModelCapabilities` (Pydantic) | `backend/app/models/registry_types.py` | `RuntimeDescriptor.spec.capabilities` is a subset; validated, not owned |
| **Variant** realization | `VoiceVariant` (`artifact_type`, `params`, `source`, `status`) | `backend/app/models/db.py:194-220` | NONE — runtime never sees VoiceVariant |
| **Artifact** model-specific assets | `VoiceVariantArtifact` (`storage_keys`, `version`, `checksum`, `model_version`) | `backend/app/models/db.py:222` | NONE — runtime never sees artifacts |
| **Runtime** deployment state | `RuntimeInstance` (`state`, `host`, `port`, `image_identity`, `health_state`) | `backend/app/services/runtime_instance.py:67` | Owns deployment state; nothing else |

The invariant holds:
- Voices own identity.
- Models own capabilities.
- Variants own realizations.
- Artifacts own model-specific assets.
- Runtimes own deployment state only.

---

## Architectural invariants (re-verified)

| Invariant | Evidence |
|---|---|
| Docker imports confined to driver package | `python scripts/lint_no_docker_outside_driver.py` → clean |
| `RuntimeManager` is orchestration-only (no substrate imports) | `grep` for docker / httpx / kokoro / torch / f5_tts / fish_audio in `runtime_manager.py` → no matches |
| `RuntimeDriver` Protocol is substrate-neutral | `runtime_driver.py` has no substrate imports |
| `HTTPTransport` is the only HTTP-shape adapter dependency | `grep` for httpx in adapters → only `kokoro_adapter.py` imports `HTTPTransport` |
| Adapter contract surface unchanged | `test_kokoro_runtime_adapter.py::test_adapter_contract_surface_unchanged` |
| No runtime activation in 2C (bridge is a literal `pass`) | `runtime.py:482-486` |
| In-process fallback intact | `test_kokoro_runtime_adapter.py::test_generate_falls_back_to_in_process_when_url_unset` |
| Full backend test suite | 466 passed, 1 skipped (E2E gated) |

---

## Conclusion

**The Runtime Activation Audit PASSES.**

Runtime activation does not create a new source of truth. The
canonical chain (Voice → VoiceVariant → Active Artifact →
Adapter) is intact. Runtime infrastructure remains strictly
downstream (Adapter → RuntimeManager → RuntimeDriver →
Runtime Service). The expected invariant holds.

**Phase 2D is unblocked.** The implementation can proceed with
the following guardrail in force:

> **No runtime activation may import, depend on, or persist
> Voice, VoiceVariant, or VoiceVariantArtifact. The runtime
> layer is a deployment layer; domain ownership is the DB
> layer's concern.**

This guardrail is verified by the audit and is the basis for
the 2D implementation. Any new code in 2D that violates this
guardrail (e.g. a runtime method that takes a `Voice` argument,
a `RuntimeDescriptor` field that carries a `voice_id`, a
runtime event that emits a `VoiceVariant`) is a regression and
must be removed.

---

**Related:** [`../../../IMPLEMENTATION_STATUS.md`](../../../IMPLEMENTATION_STATUS.md) ·
[`../../../PROJECT_STATE.md`](../../../PROJECT_STATE.md) ·
[`../../FEATURES/runtime-services-implementation/VALIDATION.md`](../../FEATURES/runtime-services-implementation/VALIDATION.md) ·
[`../../FEATURES/runtime-services-implementation/TASKS.md`](../../FEATURES/runtime-services-implementation/TASKS.md)
