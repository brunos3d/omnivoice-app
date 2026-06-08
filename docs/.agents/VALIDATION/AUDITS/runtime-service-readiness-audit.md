# Runtime Service Readiness Audit — Pre-Phase-3

> **Status:** **RUNTIME SERVICE MISSING** · **Date:** 2026-06-07
> · **Auditor:** Runtime-Service implementation agent
> · **Scope:** The actual Kokoro Runtime Service
> container, its definition, and whether the runtime-service
> path can be exercised end-to-end against a real
> `peakvox/kokoro-runtime` container.

## 1. The headline finding

The Runtime Infrastructure is **complete** (Phase 2A+2B+2C+2D
are implemented; 9 modules + 1 driver + 1 transport + 1
settings field + 1 CLI skeleton + 1 runtime-registry/
directory; 499 backend tests pass; lint clean). The
architectural invariants hold (Runtime Activation Audit,
all 7 checks PASS).

**The first concrete Runtime Service does not exist.**

Specifically:

- The descriptor at
  `runtime-registry/kokoro-82m/descriptor.json` declares
  `image.repository: peakvox/kokoro-runtime` and
  `image.tag: 0.1.0`. **No such image exists** in any
  registry, nor is it built anywhere in the repository.
- There is **no Dockerfile** for a Kokoro runtime service.
  The only Dockerfile in the repo is `backend/Dockerfile`
  (the main backend).
- There is **no `docker-compose.yml` entry** for a Kokoro
  runtime service. The repo's `docker-compose.yml`
  declares only `backend`, `minio`, and `frontend`.
- There is **no service application** (FastAPI / Flask /
  Starlette) that implements the Runtime Service Contract
  endpoints (`/health`, `/ready`, `/v1/generate`,
  `/v1/variants/build`, `/v1/metadata`).
- **`KOKORO_RUNTIME_URL` defaults to `""`** (empty). The
  `.env` file does not set it. `KokoroAdapter` reads
  `os.environ.get(KOKORO_RUNTIME_URL)` and falls through
  to the in-process `kokoro` pip package when the value
  is empty.
- **No code path instantiates `DockerRuntimeDriver` or
  constructs a `RuntimeManager`.** The
  `attach_runtime_manager()` method is never called from
  `main.py` or `model_wiring.py`. The driver and manager
  exist as production-ready code, but they are dead code
  in the current wiring.
- The **Models page Install/Activate UI** calls
  `POST /api/models/{model_id}/install` and
  `POST /api/models/{model_id}/activate`. These endpoints
  call `install_model` / `activate_model` in
  `backend/app/services/model_lifecycle.py`, which are
  **pure DB status transitions** (`UPDATE models SET
  status=...`). They do NOT touch the `RuntimeManager`.
  The CE "Ollama for Voice" install/activate flow is
  mocked (the docstring at line 57-62 explicitly says
  "the real artifact download is intentionally mocked
  for now").

**Consequence:** Every voice generation call in the
current codebase uses the in-process fallback path. The
runtime-service path is structurally complete but
operationally unreachable. The descriptor
`peakvox/kokoro-runtime:0.1.0` describes a fictional
artifact. If the manager were ever wired, the driver's
`install_runtime()` would call `client.images.pull(
"peakvox/kokoro-runtime:0.1.0")` and raise
`ImagePullError` (no such image in any registry).

---

## 2. The seven audit questions

### Q1. Is `DockerRuntimeDriver` currently operating against real Docker Engine instances or only tests/mocks?

**Status:** Driver code is production-ready; driver is
never instantiated.

- The driver's `install_runtime()` calls
  `client.images.pull(...)` against a real
  `docker.from_env()` client (`docker_runtime_driver.py:307-309`).
- The driver's `start_runtime()` calls
  `client.containers.run(...)` to create a real container
  (`docker_runtime_driver.py:356+`).
- The driver's readiness probe (`_wait_ready`) hits
  `http://<host>:<port>/ready` against the real container.
- 21 unit tests use `_MockDockerClient` and a real
  `httpx`-style probe; these tests do not require the
  docker SDK (lazy `import docker` inside `_ensure_client()`).
- **However:** `grep` for `DockerRuntimeDriver(` /
  `RuntimeManager(` / `attach_runtime_manager(` against
  `backend/app/main.py` and `backend/app/services/`
  returns **no matches outside the test files**. The
  driver and manager are never instantiated or attached at
  startup.

The driver code is real, the docker SDK is lazy-loaded,
the test suite has a comprehensive `_MockDockerClient` —
but **nothing wires the manager into the running
backend.** This is the same situation as the manager
itself in Phase 2A: the seam exists, the call site does
not.

### Q2. Is `RuntimeManager.install()` actually pulling OCI images?

**Status:** Code path is real; call site is missing.

- `RuntimeManager.install(runtime_id)` calls
  `driver.install_runtime(runtime_id, descriptor)`
  (`runtime_manager.py:198-211`).
- `DockerRuntimeDriver.install_runtime` calls
  `client.images.pull(...)` against the docker daemon
  (`docker_runtime_driver.py:303-309`).
- 12 tests in `test_runtime_manager_operations.py` use a
  fake driver; they verify the cache, the event
  publication, the error mapping — but the fake driver
  does not pull a real image.

**No real image has ever been pulled by the running
backend.** The image-pulling code path is real and
exercised in tests with a mock. No `RuntimeManager` is
ever instantiated in the running app.

### Q3. Is `RuntimeManager.start()` actually creating containers?

**Status:** Code path is real; call site is missing.

- `RuntimeManager.start(runtime_id)` calls
  `driver.start_runtime(runtime_id)`
  (`runtime_manager.py:225-231`).
- `DockerRuntimeDriver.start_runtime` calls
  `client.containers.run(image, ...)` with the
  descriptor's port bindings, env, labels, and
  restart policy.
- After start, the driver polls `/ready` on the
  container's host port until the readiness probe
  returns 200 (or `start_timeout_seconds` elapses, raising
  `RuntimeHealthFailed`).

**No container has ever been created by the running
backend.** The container-creation code path is real and
exercised in tests with a mock. `docker ps` correctly
shows no Kokoro runtime container because nothing in the
running backend instantiates the driver.

### Q4. Is the Models page Install/Activate workflow connected to `RuntimeManager` operations?

**Status:** **NOT CONNECTED.** The API exists; the
backend's install/activate path is a pure DB status
transition.

- Frontend Models page calls
  `POST /api/models/{model_id}/install` and
  `POST /api/models/{model_id}/activate` (and the
  matching deactivate, deprecate, update, remove).
- The endpoint handlers are in
  `backend/app/api/models.py:141-189`; they delegate to
  `model_lifecycle.install_model / activate_model /
  deactivate_model / update_model / remove_model`.
- `model_lifecycle.py` is a **pure DB layer** —
  `UPDATE models SET status=...` and
  `model_registry.set_status(...)`. There is no
  `RuntimeManager` import. There is no driver
  instantiation. There is no image pull. There is no
  container start.
- The docstring at `model_lifecycle.py:57-62` says
  "the real artifact download is intentionally mocked
  for now" — the CE install flow is intentionally a
  status transition, not a real runtime install.
- The runtime-registry/ directory is **not loaded at
  startup**. `grep` for `RuntimeRegistryLoader` /
  `RUNTIME_REGISTRY_PATH` against
  `backend/app/main.py` and `backend/app/services/`
  returns only the `Settings` declaration
  (`config.py:75`) and the `runtime_registry` module
  itself. **No code constructs a
  `RuntimeRegistryLoader` or builds a
  `RuntimeRegistry` from the runtime-registry/ directory.**

The Models page Install/Activate workflow is **decoupled
from the RuntimeService architecture**. Activating a
model updates a status column; it does not start a
container, pull an image, or build a runtime service.

### Q5. Does a Kokoro Runtime Service implementation exist anywhere in the repository?

**Status:** **NO.**

`grep` for `peakvox-kokoro-runtime` / `kokoro-runtime
service` / `kokoro_runtime_service` across the entire
repository returns:

- `backend/tests/test_kokoro_e2e_runtime.py` — test
  fixture (no implementation)
- `docs/.agents/SPECS/FEATURES/runtime-services-implementation/TASKS.md:308`
  — spec text "docker compose up peakvox-backend
  peakvox-kokoro-runtime"
- `docs/.agents/SPECS/FEATURES/runtime-services-implementation/VALIDATION.md:137`
  — validation text
- `docs/.agents/SPECS/FEATURES/models-as-runtime-services/TASKS.md:137`
  — spec text "peakvox/kokoro-runtime (HTTP server
  wrapping the existing `kokoro` pip package)"

**No Python module, no FastAPI app, no Flask app, no
ASGI/WSGI server, no Dockerfile, no compose service, no
shell script, no Kubernetes manifest, no Helm chart, no
systemd unit, no start script, no Makefile target exists
for the Kokoro Runtime Service.**

The descriptor describes a fictional container. The
spec describes a fictional service. The audit
identifies a real gap.

### Q6. Is there any Dockerfile, compose file, OCI image definition, or runtime service application for Kokoro?

**Status:** **NO.**

- `glob '**/Dockerfile*'` returns only
  `backend/Dockerfile` (the main backend, building the
  FastAPI app — not a runtime service).
- `glob '**/docker-compose*.yml'` returns only the
  root `docker-compose.yml`, which declares
  `backend`, `minio`, `frontend` — no `peakvox-kokoro-runtime`
  service.
- `glob 'runtime-registry/**/*'` returns only
  `runtime-registry/kokoro-82m/descriptor.json` —
  **only the descriptor, no Dockerfile, no compose
  overlay, no source.**
- `glob '**/kokoro_runtime*'` and
  `glob 'kokoro_runtime/**/*'` return **no results**.

There is no OCI image definition (Dockerfile) for a
Kokoro runtime service, no compose overlay, no
Kubernetes/Helm manifest, no runtime service source
tree. The `peakvox/kokoro-runtime:0.1.0` image
referenced in the descriptor has never been built.

### Q7. Is `KOKORO_RUNTIME_URL` currently pointing to a real runtime endpoint or only supporting fallback mode?

**Status:** **Fallback mode only.**

- `Settings.KOKORO_RUNTIME_URL: str = ""`
  (`config.py:67`).
- The `.env` file does not set
  `KOKORO_RUNTIME_URL` (`grep` against `.env`
  returns no matches).
- The `.env.example` file does not set
  `KOKORO_RUNTIME_URL` either.
- `KokoroAdapter._runtime_service_enabled()` returns
  `bool(os.environ.get("KOKORO_RUNTIME_URL", "").strip())`
  — **false** in the default venv.
- The adapter's dispatch falls through to the in-process
  `kokoro` package (lazy import) on every call.

Every voice generation in the current codebase uses
the in-process fallback. The runtime-service dispatch
exists in the code; it is never taken.

---

## 3. Gap analysis (one-line summary)

**Infrastructure Completed** ✅
**Runtime Service Missing** ❌
**Runtime Service Partial** —
**Runtime Service Complete** —

| Surface | Status |
|---|---|
| Runtime types (descriptor, instance, health, errors) | ✅ |
| RuntimeDriver Protocol | ✅ |
| RuntimeRegistry + Loader | ✅ |
| RuntimeEventBus | ✅ |
| RuntimeManager (orchestration only) | ✅ |
| `RuntimeManager` instance cache + CE operations | ✅ |
| `DockerRuntimeDriver` (lazy `docker.from_env()`) | ✅ |
| `lint_no_docker_outside_driver.py` | ✅ |
| `HTTPTransport` (pure HTTP abstraction) | ✅ |
| `KokoroAdapter` `KOKORO_RUNTIME_URL` integration | ✅ |
| `Settings.KOKORO_RUNTIME_URL` / `RUNTIME_REGISTRY_PATH` | ✅ |
| 2A bridge activation (observability) | ✅ |
| `RuntimeOperator` CLI skeleton | ✅ |
| `runtime-registry/kokoro-82m/descriptor.json` | ✅ |
| Kokoro Runtime Service Dockerfile | ❌ |
| Kokoro Runtime Service HTTP server app | ❌ |
| Kokoro Runtime Service docker-compose entry | ❌ |
| `RuntimeRegistry` loaded at backend startup | ❌ |
| `DockerRuntimeDriver` instantiated at backend startup | ❌ |
| `RuntimeManager` attached to `PeakVoxRuntime` singleton | ❌ |
| Models page Install/Activate calls `RuntimeManager.install/start` | ❌ |
| `KOKORO_RUNTIME_URL` pointing to a real endpoint | ❌ (empty by default) |
| E2E audio generation through a real `peakvox/kokoro-runtime` container | ❌ |

---

## 4. The four unresolved wiring gaps

The audit identifies four distinct wiring gaps. Each
must be closed before Phase 3 can be considered
complete.

### Gap 1 — No Kokoro Runtime Service container

There is no `peakvox/kokoro-runtime:0.1.0` image and
no source tree to build it. The descriptor is
describing a fictional artifact.

### Gap 2 — Runtime-registry is not loaded at startup

`Settings.RUNTIME_REGISTRY_PATH` points to the
in-repo `runtime-registry/` directory, but no code
constructs a `RuntimeRegistryLoader` or builds a
`RuntimeRegistry` from it. The descriptor file
sits on disk; nothing reads it.

### Gap 3 — RuntimeManager is never instantiated or attached

`attach_runtime_manager()` is a public method on
`PeakVoxRuntime`, but no production code calls it.
There is no singleton `RuntimeManager` constructed
at startup. The manager and driver are
production-ready code that is never wired.

### Gap 4 — Models page install/activate does not call RuntimeManager

The CE install/activate UI flow updates a DB
status column. It does not call
`runtime_manager.install(runtime_id)` /
`runtime_manager.start(runtime_id)`. The
`install_model` / `activate_model` functions in
`model_lifecycle.py` are intentionally mocked
status transitions; they are NOT the
RuntimeService install/activate flow.

---

## 5. Phase 3 implementation plan

> **Goal of Phase 3:** Make the first descriptor in
> `runtime-registry/` (`kokoro-82m`) capable of
> launching a real runtime container and serving
> real inference through `HTTPTransport`. The goal
> is **not** more infrastructure. The goal is
> **a working runtime service.**

This plan is **NOT IMPLEMENTED YET**. It is a
proposal for the user's review. No code has been
written for Phase 3 in this audit.

### 3.1 — Build the Kokoro Runtime Service image

Files:

- `runtime-registry/kokoro-82m/Dockerfile` — minimal
  Python image with `kokoro` + a small FastAPI
  service app; exposes port 8000; `CMD` runs the
  service.
- `runtime-registry/kokoro-82m/server.py` —
  FastAPI app implementing the Runtime Service
  Contract (5 endpoints: `/health`, `/ready`,
  `/v1/generate`, `/v1/variants/build`,
  `/v1/metadata`). The `/v1/generate` endpoint
  wraps the `kokoro` package's `KPipeline`. The
  response shape matches ADR-0017 §6.3 (audio
  base64, duration, logs).
- `runtime-registry/kokoro-82m/requirements.txt`
  — pinned `kokoro` + `fastapi` + `uvicorn` +
  `soundfile` + `numpy`.
- `runtime-registry/kokoro-82m/README.md` —
  operator notes: how to build, run, test.

TDD shape:

- A build test that runs `docker build
  runtime-registry/kokoro-82m/` and produces a
  valid image.
- A container test that runs the image and
  verifies `GET /health` returns 200 and
  `GET /ready` returns 200.
- An inference test that runs the image and
  verifies `POST /v1/generate` with a fixture
  payload produces real audio (base64-decoded
  bytes match an expected length and WAV
  header).

This is the **first time** a real OCI image is
built in this repository's history. The
`docker_runtime_driver.py` code is exercised
against a real image for the first time.

### 3.2 — Wire `RuntimeRegistry` + `RuntimeManager` into backend startup

Files:

- `backend/app/services/runtime_wiring.py` (new)
  — constructs a `RuntimeRegistryLoader`, loads
  the registry from
  `Settings.RUNTIME_REGISTRY_PATH`, constructs a
  `RuntimeManager` with the
  `DockerRuntimeDriver` (lazy — only
  instantiates the driver when the user explicitly
  enables runtime services), and attaches the
  manager to the `runtime` singleton.
- `backend/app/main.py` — calls the new
  `wire_runtime_manager()` inside the lifespan
  startup, AFTER `wire_runtime()`. The wiring is
  conditional on `settings.KOKORO_RUNTIME_URL`
  being set OR a dedicated
  `settings.RUNTIME_SERVICE_ENABLED` flag.
- `backend/app/core/config.py` — adds
  `RUNTIME_SERVICE_ENABLED: bool = False` (CE
  default off; opt-in).

TDD shape:

- A wiring test that verifies
  `wire_runtime_manager()` constructs a manager,
  loads the registry from a temp directory, and
  attaches it to the `runtime` singleton.
- An integration test that runs the full wiring
  against a fixture registry and verifies
  `runtime._runtime_manager is not None`.

### 3.3 — Connect the Models page Install/Activate workflow to `RuntimeManager`

Files:

- `backend/app/api/models.py` — when the CE
  runtime services are enabled, the
  `POST /api/models/{model_id}/install` and
  `POST /api/models/{model_id}/activate` endpoints
  ALSO call the `RuntimeManager.install()` /
  `RuntimeManager.start()` (for the runtime
  descriptors that bind to this model).
- `backend/app/services/model_lifecycle.py` — the
  status transition is preserved (DB is the
  source of truth for lifecycle); the
  RuntimeManager operations are layered ON TOP
  (best-effort: if the runtime is not available,
  the status transition still succeeds; the
  runtime will be installed/started when the
  next runtime-registry refresh happens).

TDD shape:

- A test that verifies a successful install
  call updates the DB status AND calls
  `runtime_manager.install(runtime_id)`.
- A test that verifies a runtime install
  failure does NOT block the DB status
  transition (the DB is the source of truth).

### 3.4 — E2E validation: docker-compose up + real audio

Files:

- `docker-compose.yml` — adds a
  `peakvox-kokoro-runtime` service that builds
  the image from
  `runtime-registry/kokoro-82m/Dockerfile` and
  exposes port 8000 on the backend's docker
  network.
- `.env.example` — documents
  `KOKORO_RUNTIME_URL=http://peakvox-kokoro-runtime:8000`
  for the docker-compose path.
- `backend/tests/test_kokoro_e2e_runtime.py` —
  the existing gated E2E test is enabled
  against the docker-compose CI lane. The
  test now produces real audio through the
  runtime service, end-to-end.

TDD shape:

- The existing gated test
  (`test_kokoro_runtime_service_e2e_generates_audio`)
  is un-skipped in the docker-compose CI lane.
- A new G6 report
  (`kokoro-runtime-validation-report.md` already
  exists; update it) is rewritten with real
  audio data (sample rate, duration, byte
  size, file path) and the docker-compose
  command that produced it.

### 3.5 — Provider-validated G6 update + G7/G8

Files:

- `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-runtime-validation-report.md`
  — updated with real E2E data (audio file
  produced, container lifecycle, docker-compose
  command, sample duration, byte size).
- `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-g7-performance-report.md`
  — new report: RTF, VRAM, load time.
- `docs/.agents/VALIDATION/PROVIDER_VALIDATIONS/kokoro-g8-error-recovery-report.md`
  — new report: crashed container recovery,
  network partition recovery, runtime health
  failure recovery.

### 3.6 — State file updates (final)

`IMPLEMENTATION_STATUS.md`, `NEXT_TASK.md`,
`ACTIVE_WORK.md`, `CURRENT_CONTEXT.md`,
`PROJECT_STATE.md`, `ROADMAP/CURRENT_PHASE.md` —
all promoted to reflect Phase 3 complete. ADR-0016
+ ADR-0017 rows flip to "VALIDATED" (the first
runtime-service path is provider-validated). Phase 4
(F5-TTS reference) is unblocked.

### Definition of done — Phase 3

- `docker compose up peakvox-backend
  peakvox-kokoro-runtime` produces a working
  stack.
- `KOKORO_RUNTIME_URL` is set to
  `http://peakvox-kokoro-runtime:8000` in the
  compose `.env`.
- `POST /api/generate` produces real audio
  through the runtime service (verified by
  `test_kokoro_e2e_runtime.py` in the
  docker-compose CI lane).
- The in-process path is still the default when
  `KOKORO_RUNTIME_URL` is empty (no behavior
  regression).
- G6 (real audio E2E) ✅; G7 (Performance) ✅;
  G8 (Error recovery) ✅.
- Phase 4 (F5-TTS) is unblocked: the
  `KokoroAdapter` is the reference, and the
  `peakvox/kokoro-runtime` is the reference
  service.

---

## 6. Risks and unknowns

### R-1. Kokoro weights

The Kokoro-82M weights are auto-downloaded by the
`kokoro` pip package from Hugging Face on first
inference. The runtime service container will need
to pre-download or lazy-download these weights
inside the container. The size is ~80MB. The
download path is well-trodden (the in-process
adapter uses the same path).

### R-2. Spacy model dependency

`kokoro` requires the `en_core_web_sm` Spacy
model. This is auto-downloaded on first use. The
runtime service container must include the Spacy
model in the image OR auto-download it on startup.

### R-3. CPU-only vs GPU image

Kokoro-82M runs on CPU (it is 82M params, designed
to be CPU-capable). The descriptor declares
`gpu: optional`. The first runtime service image
is CPU-only. A GPU variant is a future
deliverable.

### R-4. Image digest pinning

The descriptor's `image.digest` is null (the
descriptor pins only the tag `0.1.0`). A future
revision should pin a specific
`sha256:...` digest for reproducibility. The
`DockerRuntimeDriver.install_runtime()` already
supports digest-pinned pulls (lines 306-309).

### R-5. The Models page UI is currently a mock

The CE install/activate UI is a status-transition
mock. Wiring it to the RuntimeManager (Gap 4) is
a behavior change for CE users. It must be
gated on `RUNTIME_SERVICE_ENABLED` so the
default CE experience is unchanged.

---

## 7. Conclusion

**The Phase 2 infrastructure is complete and
correct.** The Runtime Activation Audit (all 7
checks PASS) confirms the canonical chain
(Voice → VoiceVariant → Active Artifact →
Adapter) is intact and runtime infrastructure is
strictly downstream.

**The first concrete Runtime Service does not
exist.** The descriptor describes a fictional
container. The driver is real but never
instantiated. The manager is real but never
attached. The HTTP transport is real but never
exercised against a real endpoint. The Models
page install/activate workflow is a DB status
mock, not a RuntimeManager flow.

**Phase 3 must build the first real runtime
service.** The plan in §5 is the proposal:
build `peakvox/kokoro-runtime:0.1.0`, wire the
RuntimeManager into backend startup, connect
the Models page to the manager, and validate
end-to-end with `docker compose`. The plan is
**not implemented yet** — it is a proposal for
the user's review.

**The infrastructure is solid.** The remaining
work is **operational**, not architectural.
Phase 3 is a focused, contained effort: one
Dockerfile, one FastAPI service app, four
wiring touchpoints, and one docker-compose
overlay. The infrastructure that Phase 3 lands
on was designed for this moment; no
architectural rework is needed.

---

**Related:** [`runtime-activation-audit.md`](runtime-activation-audit.md) ·
[`../../SPECS/FEATURES/runtime-services-implementation/SPEC.md`](../../SPECS/FEATURES/runtime-services-implementation/SPEC.md) ·
[`../../SPECS/FEATURES/runtime-services-implementation/TASKS.md`](../../SPECS/FEATURES/runtime-services-implementation/TASKS.md) ·
[`../PROVIDER_VALIDATIONS/kokoro-runtime-validation-report.md`](../PROVIDER_VALIDATIONS/kokoro-runtime-validation-report.md)
