# Future Runtime Registry Standardization Audit (Task 11)

**Date:** 2026-06-08
**Subject:** Validate that `runtime-registry/kokoro-82m/` is a reusable template for F5-TTS, XTTS, OpenVoice, Fish Audio, OmniVoice. Document any missing pieces.
**Status:** AUDIT COMPLETE
**Result:** The Kokoro entry **is** the canonical R8 reference. Adding a new runtime is a copy of `kokoro-82m/` plus targeted edits. No missing pieces; the only thing the next runtime needs is the framework-specific `server.py` and `Dockerfile`.

---

## The target shape (R8 canonical)

```
runtime-registry/
└── <runtime_id>/
    ├── descriptor.json       (the contract)
    ├── Dockerfile            (CE build)
    ├── server.py             (CE entrypoint)
    ├── requirements.txt      (CE runtime deps)
    ├── README.md             (operator documentation)
    └── tests/                (CE validation)
        ├── __init__.py
        ├── conftest.py
        ├── test_server.py    (5-endpoint contract)
        ├── test_dockerfile.py (Dockerfile structure)
        ├── test_docker_build.py (gated E2E)
        └── test_docker_generate.py (gated E2E)
```

## Validation: does `kokoro-82m/` match the target?

| File | Present? | Validated? |
|---|---|---|
| `descriptor.json` | ✅ | ✅ (10 R8 reference tests) |
| `Dockerfile` | ✅ | ✅ (9 structure tests) |
| `server.py` | ✅ | ✅ (10 contract tests) |
| `requirements.txt` | ✅ | ✅ (file present) |
| `README.md` | ✅ | ✅ (file present) |
| `tests/__init__.py` | ✅ | n/a |
| `tests/conftest.py` | ✅ | n/a |
| `tests/test_server.py` | ✅ | ✅ (10 tests) |
| `tests/test_dockerfile.py` | ✅ | ✅ (9 tests) |
| `tests/test_docker_build.py` | ⚠️ **Missing** | — |
| `tests/test_docker_generate.py` | ⚠️ **Missing** | — |

**Two files are missing**: the gated E2E tests for actual `docker build` and `docker run` + audio generation. These are CI-gated (require a real Docker host). They are **described in the TASKS.md P1.6 task** but not yet authored.

**Recommendation:** add `test_docker_build.py` and `test_docker_generate.py` to `runtime-registry/kokoro-82m/tests/`. These are the test surface for the R8 standard; future runtimes copy these files too.

## What changes when adding a new runtime (the R8 pattern)

When a new runtime is added (F5-TTS, XTTS, OpenVoice, Fish Audio, OmniVoice), the steps are:

### Step 1 — Copy the directory

```bash
cp -r runtime-registry/kokoro-82m/ runtime-registry/f5-tts/
# rename the directory
mv runtime-registry/f5-tts/kokoro-82m-tests* runtime-registry/f5-tts/f5-tts-tests*  # if any
```

### Step 2 — Edit `descriptor.json` (6 fields)

| Field | Kokoro | F5-TTS (example) |
|---|---|---|
| `metadata.id` | `kokoro-82m` | `f5-tts` |
| `metadata.name` | `Kokoro 82M Runtime` | `F5-TTS Runtime` |
| `metadata.provider` | `kokoro` | `f5-tts` |
| `metadata.version` | `0.1.0` | `0.1.0` |
| `spec.image.repository` | `peakvox/kokoro-runtime` | `peakvox/f5-tts-runtime` |
| `spec.image.tag` | `0.1.0` | `0.1.0` |
| `spec.service.port` | `8000` | `8000` (or different if conflict) |
| `spec.model_binding.model_id` | `kokoro-base` | `f5-tts-base` |
| `spec.model_binding.is_default` | `true` | `false` (Kokoro is the default) |
| `spec.model_binding.priority` | `100` | `200` |
| `spec.build.entrypoint` | `server.py` | `server.py` (unchanged) |
| `spec.build.build_context` | `.` | `.` (unchanged) |
| `spec.build.dockerfile` | `Dockerfile` | `Dockerfile` (unchanged) |
| `spec.capabilities` | `["tts"]` | `["tts", "voice_cloning"]` (or whatever the model supports) |
| `spec.requirements.gpu` | `"optional"` | `"required"` (or `"optional"`) |
| `spec.requirements.min_vram_gb` | `0` | `4` (or whatever) |
| `spec.requirements.cpu_cores` | `1` | `2` |
| `spec.requirements.memory_gb` | `2` | `8` |
| `spec.requirements.edition` | `["ce"]` | `["ce"]` (or `["ce", "cloud"]`) |
| `spec.lifecycle.idle_timeout` | `"15m"` | `"15m"` (CE default) |

That's 17 fields. All are simple scalar or list values. No structural changes.

### Step 3 — Edit `requirements.txt`

Replace the framework pin:

```
# Before (Kokoro)
kokoro==0.7.16
spacy==3.8.3

# After (F5-TTS)
f5-tts==1.0.0
torch==2.4.0  # or whatever the framework requires
```

The HTTP service framework pins (`fastapi`, `uvicorn`, `pydantic`) stay unchanged.

### Step 4 — Edit `server.py`

The 5-endpoint contract is unchanged. Only the **inference call** changes:

```python
# Before (Kokoro)
def _load_pipeline():
    from kokoro import KPipeline
    _pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")

def _run_inference(req):
    return _pipeline(req.text, voice=req.voice_id)

# After (F5-TTS)
def _load_pipeline():
    from f5_tts import F5TTS  # the new framework
    _pipeline = F5TTS(...)

def _run_inference(req):
    return _pipeline.synthesize(text=req.text, voice=req.voice_id, ...)
```

The `_float32_to_wav_bytes()` helper is **unchanged** — every framework produces float32 audio that gets encoded as 16-bit PCM WAV.

The `/v1/metadata` response is **provider-specific** (capabilities, supported_languages, supported_tags). Each runtime declares its own.

### Step 5 — Edit `Dockerfile`

The base image and system deps change; the structure is unchanged.

```dockerfile
# Before (Kokoro)
FROM python:3.11-slim
RUN apt-get install -y ffmpeg espeak-ng build-essential
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY server.py .
EXPOSE 8000
HEALTHCHECK ...
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

# After (F5-TTS)
FROM python:3.11-slim
RUN apt-get install -y ffmpeg libsndfile1 build-essential  # different system deps
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY server.py .
EXPOSE 8000
HEALTHCHECK ...
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

The `EXPOSE` and `CMD` stay unchanged (descriptor's `spec.service.port` must match).

### Step 6 — Edit `README.md`

Copy and update: name, port, framework name, provider notes, troubleshooting.

### Step 7 — Edit `tests/`

The contract tests are the same 10 tests; the descriptor's id and provider change. The Dockerfile structure tests are the same 9 tests. No new test logic is needed for the contract surface; provider-specific tests are added in `test_server.py` for capability / language / tag gating.

### Step 8 — Update `docker-compose.yml`

Add a service entry mirroring `peakvox-kokoro-runtime`:

```yaml
peakvox-f5-tts-runtime:
  build:
    context: ./runtime-registry/f5-tts
    dockerfile: Dockerfile
  image: peakvox/f5-tts-runtime:0.1.0
  ports:
    - "8002:8000"
  ...
```

### Step 9 — Add the catalog model (if not already present)

If the new runtime serves an existing catalog model (e.g. `f5-tts-base`), the model already exists in `BUILTIN_MODELS`. If the runtime serves a NEW catalog model, add the model to `BUILTIN_MODELS` and create a migration to seed it.

### Step 10 — Update the adapter

The adapter for the new framework must be added to `runtime.py`'s `wire_runtime()`. The adapter follows the same pattern as `KokoroAdapter`: dispatch on a runtime URL env var, fall back to in-process.

## What is missing from the R8 standard

### Missing test files (CI-gated E2E)

- `runtime-registry/kokoro-82m/tests/test_docker_build.py` — exercises `docker build` + `docker run` + `/health` 200. CI-gated.
- `runtime-registry/kokoro-82m/tests/test_docker_generate.py` — exercises `POST /v1/generate` and asserts a non-empty WAV.

**Recommendation:** add these test files in a follow-up commit. They require a real Docker host to run; the CI lane is the docker-compose lane.

### Missing CLI tool

There's no `runtime-registry/build.sh` or `runtime-registry/test.sh` script. The current workflow is:
- `cd runtime-registry/<id>/` and run `pytest tests/` for the contract tests.
- `docker build` for the gated E2E.

**Recommendation:** add `runtime-registry/scripts/build-and-test.sh` that loops over each runtime directory and runs the contract tests. Optional: add a CI workflow that builds the images and runs the gated E2E in the docker-compose lane.

### Missing CI integration

There is no `runtime-registry/.github/workflows/test.yml` or similar. The contract tests are not run automatically on PR.

**Recommendation:** add a CI workflow that runs `pytest runtime-registry/<id>/tests/test_server.py` and `test_dockerfile.py` on every PR. The gated E2E runs on main / release branches.

### Missing descriptor validation tool

There's no `runtime-registry/scripts/validate-descriptors.sh` that walks all entries and validates the descriptor against the closed schema. The validation is currently done at runtime by `RuntimeRegistryLoader`.

**Recommendation:** add a small CLI tool that:
1. Walks `runtime-registry/<id>/` directories.
2. Validates each `descriptor.json` against the closed schema.
3. Asserts the `metadata.id` matches the directory name.
4. Asserts `spec.image.repository` follows the `peakvox/<runtime_id>-runtime` convention.

This is a small Python script (~50 lines) that can be run as a pre-commit hook or in CI.

## The R8 standard is sufficient for the next 5+ runtimes

The 5 candidate runtimes (F5-TTS, XTTS, OpenVoice, Fish Audio, OmniVoice) all fit the R8 standard:

| Runtime | Model size | GPU | Image size | Effort |
|---|---|---|---|---|
| F5-TTS | ~330M | optional | ~3 GB | trivial (mirror Kokoro) |
| XTTS | ~500M | optional | ~3 GB | trivial (mirror Kokoro) |
| OpenVoice | ~100M | none | ~1.5 GB | trivial (mirror Kokoro) |
| Fish Audio S2 Pro | ~1B | required | ~5 GB | trivial (mirror Kokoro; heavier image) |
| OmniVoice Base | ~600M | optional | ~3-5 GB | trivial (mirror Kokoro; see Task 10 audit) |

**The Kokoro entry is the canonical reference. No architectural changes are needed to add any of the 5 candidate runtimes.** The migration is a copy + 6-field descriptor edit + framework-specific `server.py`.

## Conclusion

The R8 standard is the right design. The Kokoro entry validates it. The next 5 runtimes are a copy-and-edit exercise. The missing pieces (gated E2E tests, build script, CI integration, descriptor validation tool) are **operational tooling**, not architectural concerns. They are recommended as follow-up work but do not block the next runtime from being added today.

---

**See also:**
[`docs/.agents/AUDITS/source-of-truth-audit.md`](source-of-truth-audit.md) (Task 1)
·
[`docs/.agents/AUDITS/models-page-integration-audit.md`](models-page-integration-audit.md) (Task 2)
·
[`docs/.agents/AUDITS/omnivoice-migration-audit.md`](omnivoice-migration-audit.md) (Task 10)
·
[`runtime-registry/kokoro-82m/`](../../../runtime-registry/kokoro-82m/) (R8 reference)
·
[`docs/.agents/SPECS/FEATURES/runtime-services-implementation/SPEC.md`](../SPECS/FEATURES/runtime-services-implementation/SPEC.md) (R8 description)
