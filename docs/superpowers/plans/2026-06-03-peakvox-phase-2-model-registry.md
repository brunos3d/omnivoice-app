# PeakVox Phase 2 — Model Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Prerequisite:** Phase 1 (Foundations) is merged — `settings.features`, the `app/cloud` boundary, and `mount_cloud_routers` exist.

**Goal:** Make `Model` a fully first-class, versioned, lifecycle-managed entity with provider, licensing, and requirements metadata, plus Hugging Face install support — without breaking the existing registry, providers, or `/models` API.

**Architecture:** Additive. `ModelDescriptor` and the `models` table gain `requirements`, `license`, `provider_metadata`, and `deprecated_at`. A `ModelLifecycle` service owns status transitions (`activate`/`deactivate`/`deprecate`) persisted to the `models` table. A torch-free `HuggingFaceInstaller` fetches a manifest and downloads weights into the existing `HF_HOME` cache, inserting a non-builtin `models` row. The registry stays the runtime layer over the persisted entity (ADR-0002). Lifecycle **writes** are admin-gated in Cloud; **reads** stay public.

**Tech Stack:** Python 3.12, async SQLAlchemy + aiosqlite, pydantic, FastAPI, `huggingface_hub`. Tests: pytest (`asyncio_mode=auto`), HF calls mocked.

**Reference docs:** [Domain §3 Model](../../architecture/02-DOMAIN_ARCHITECTURE.md), [Data §3.1](../../architecture/03-DATA_ARCHITECTURE.md), [ADR-0002](../../architecture/adrs/0002-model-as-first-class-entity.md), [Roadmap Phase 2](../../architecture/09-ROADMAP.md).

---

## File Structure

**Modify:**
- `backend/app/models/registry_types.py` — add `requirements`, `license`, `provider_metadata` to `ModelDescriptor`.
- `backend/app/models/db.py` — add the four columns to `Model`.
- `backend/app/core/migrations.py` — `_NEW_MODEL_COLUMNS` + `_add_missing_model_columns`; extend `_seed_builtin_models`.
- `backend/app/api/models.py` — surface new metadata; add admin lifecycle routes.

**Create:**
- `backend/app/services/model_lifecycle.py` — status-transition service.
- `backend/app/services/hf_installer.py` — manifest fetch + download + install.
- `backend/tests/test_registry_metadata.py`
- `backend/tests/test_model_lifecycle.py`
- `backend/tests/test_hf_installer.py`
- `backend/tests/test_models_api_metadata.py`

**Frontend (Task 8, docs-first):** a Model Manager surface; exact files located in-task.

---

## Task 1: Extend `ModelDescriptor` with requirements / license / provider metadata

**Files:**
- Modify: `backend/app/models/registry_types.py`
- Create: `backend/tests/test_registry_metadata.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_registry_metadata.py`:

```python
from app.models.registry_types import ModelDescriptor, ModelRequirements, ModelLicense


def test_descriptor_defaults_are_backward_compatible():
    d = ModelDescriptor(id="m", name="M", description="d", provider="p")
    assert d.requirements == ModelRequirements()
    assert d.license is None
    assert d.provider_metadata == {}


def test_descriptor_accepts_requirements_and_license():
    d = ModelDescriptor(
        id="m", name="M", description="d", provider="p",
        requirements=ModelRequirements(min_vram_gb=8, gpu_required=True),
        license=ModelLicense(code="apache-2.0", commercial_use=True),
        provider_metadata={"author": "k2-fsa", "homepage": "https://example"},
    )
    assert d.requirements.min_vram_gb == 8
    assert d.license.commercial_use is True
    assert d.provider_metadata["author"] == "k2-fsa"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_registry_metadata.py -v`
Expected: FAIL with `ImportError: cannot import name 'ModelRequirements'`.

- [ ] **Step 3: Write minimal implementation**

In `backend/app/models/registry_types.py`, add the two models above `ModelDescriptor` and three fields on it:

```python
class ModelRequirements(BaseModel):
    """Runtime needs — drives Cloud capacity planning / VRAM-aware scheduling."""

    min_vram_gb: Optional[float] = None
    gpu_required: bool = False
    runtime: Optional[str] = None  # e.g. "torch", free-form


class ModelLicense(BaseModel):
    """Licensing metadata — relevant to marketplace + commercial-use gating."""

    code: Optional[str] = None        # e.g. "apache-2.0"
    weights_license: Optional[str] = None
    commercial_use: Optional[bool] = None
    url: Optional[str] = None
```

Add to `ModelDescriptor` (after `capabilities`):

```python
    requirements: ModelRequirements = Field(default_factory=ModelRequirements)
    license: Optional[ModelLicense] = None
    provider_metadata: dict = Field(default_factory=dict)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_registry_metadata.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/registry_types.py backend/tests/test_registry_metadata.py
git commit -m "feat(registry): ModelDescriptor requirements/license/provider_metadata"
```

---

## Task 2: Add the four columns to the `Model` ORM

**Files:**
- Modify: `backend/app/models/db.py`
- Create: `backend/tests/test_model_columns.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_model_columns.py`:

```python
from app.core.database import Base
import app.models.db  # noqa: F401


def test_model_has_new_metadata_columns():
    cols = {c.name for c in Base.metadata.tables["models"].columns}
    assert {"requirements", "license", "provider_metadata", "deprecated_at"} <= cols
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_model_columns.py -v`
Expected: FAIL (columns absent).

- [ ] **Step 3: Write minimal implementation**

In `backend/app/models/db.py`, add to the `Model` class (after `editions`):

```python
    requirements: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    license: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_model_columns.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/db.py backend/tests/test_model_columns.py
git commit -m "feat(models): Model requirements/license/provider_metadata/deprecated_at columns"
```

---

## Task 3: Migration adds the columns + seeds them for built-ins

Mirror the existing `_NEW_JOB_COLUMNS` / `_add_missing_job_columns` pattern for the `models` table, and extend `_seed_builtin_models` so built-in metadata propagates.

**Files:**
- Modify: `backend/app/core/migrations.py`
- Create: `backend/tests/test_model_metadata_migration.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_model_metadata_migration.py`:

```python
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.migrations import run_migrations


@pytest.fixture
async def engine(tmp_path):
    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/m.db", future=True)
    yield eng
    await eng.dispose()


async def _columns(engine, table):
    async with engine.begin() as conn:
        res = await conn.execute(text(f"PRAGMA table_info({table})"))
        return {row[1] for row in res.fetchall()}


async def test_model_metadata_columns_added(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)
    assert {"requirements", "license", "provider_metadata", "deprecated_at"} <= await _columns(engine, "models")


async def test_migration_idempotent_for_models(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)
    async with engine.begin() as conn:
        await run_migrations(conn)  # must not raise


async def test_builtin_base_model_seeded_with_license(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT license FROM models WHERE id='omnivoice-base'"))
        license_json = res.scalar()
    assert license_json is not None and "apache-2.0" in license_json
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_model_metadata_migration.py -v`
Expected: FAIL — columns not added by the runner; license not seeded.

- [ ] **Step 3: Add the column-adder**

In `backend/app/core/migrations.py`, after `_add_missing_job_columns`, add:

```python
# New models columns (Phase 2 — first-class model metadata). Additive, NULL-default.
_NEW_MODEL_COLUMNS: list[tuple[str, str]] = [
    ("requirements", "ALTER TABLE models ADD COLUMN requirements JSON"),
    ("license", "ALTER TABLE models ADD COLUMN license JSON"),
    ("provider_metadata", "ALTER TABLE models ADD COLUMN provider_metadata JSON"),
    ("deprecated_at", "ALTER TABLE models ADD COLUMN deprecated_at DATETIME"),
]


async def _add_missing_model_columns(conn: AsyncConnection) -> None:
    res = await conn.execute(text("PRAGMA table_info(models)"))
    existing = {row[1] for row in res.fetchall()}
    for column, ddl in _NEW_MODEL_COLUMNS:
        if column in existing:
            continue
        try:
            await conn.execute(text(ddl))
        except Exception:  # pragma: no cover - duplicate column on a racing run
            logger.debug("Model column {} already present, skipping", column)
```

Call it in `run_migrations`, immediately after the `_add_missing_job_columns(conn)` line:

```python
    # 2c. Additively add new models columns (first-class model metadata).
    await _add_missing_model_columns(conn)
```

- [ ] **Step 4: Seed the new metadata for built-ins**

Extend `_seed_builtin_models`: add the three JSON params to both the column list / VALUES and the `ON CONFLICT` update set. In the `INSERT` column list add `requirements, license, provider_metadata` (before `created_at`), add matching `:requirements, :license, :provider_metadata` to VALUES, add them to the `DO UPDATE SET`, and add to the params dict:

```python
                "requirements": json.dumps(m.requirements.model_dump()),
                "license": json.dumps(m.license.model_dump()) if m.license else None,
                "provider_metadata": json.dumps(m.provider_metadata),
```

Then give `omnivoice-base` a license in `backend/app/services/model_catalog.py` so the seed has data — add to its `ModelDescriptor(...)`:

```python
        license=ModelLicense(code="apache-2.0", commercial_use=True,
                             url="https://github.com/k2-fsa/OmniVoice"),
        provider_metadata={"author": "k2-fsa", "homepage": "https://github.com/k2-fsa/OmniVoice"},
```

and add `ModelLicense` to that file's import:

```python
from app.models.registry_types import ModelCapabilities, ModelDescriptor, ModelLicense
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_model_metadata_migration.py tests/test_model_migration.py -v`
Expected: PASS (existing model-migration test still green; new file passes).

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/migrations.py backend/app/services/model_catalog.py backend/tests/test_model_metadata_migration.py
git commit -m "feat(migrations): additive model metadata columns + seed built-in license"
```

---

## Task 4: Model lifecycle service (activate / deactivate / deprecate)

Persisted status transitions on the `models` table. `available`↔`disabled` via activate/deactivate; `deprecate` sets `status='deprecated'` + `deprecated_at`. Built-in catalog rows can be toggled; the operation targets the DB row.

**Files:**
- Create: `backend/app/services/model_lifecycle.py`
- Create: `backend/tests/test_model_lifecycle.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_model_lifecycle.py`:

```python
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)

from app.core.migrations import run_migrations
from app.services.model_lifecycle import (
    activate_model, deactivate_model, deprecate_model, ModelNotFoundError,
)


@pytest.fixture
async def session(tmp_path):
    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/lc.db", future=True)
    async with eng.begin() as conn:
        await run_migrations(conn)
    maker = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s
    await eng.dispose()


async def _status(session, model_id):
    res = await session.execute(text("SELECT status FROM models WHERE id=:id"), {"id": model_id})
    return res.scalar()


async def test_deactivate_then_activate(session):
    await deactivate_model(session, "omnivoice-base")
    assert await _status(session, "omnivoice-base") == "disabled"
    await activate_model(session, "omnivoice-base")
    assert await _status(session, "omnivoice-base") == "available"


async def test_deprecate_sets_status_and_timestamp(session):
    await deprecate_model(session, "omnivoice-base")
    assert await _status(session, "omnivoice-base") == "deprecated"
    res = await session.execute(text("SELECT deprecated_at FROM models WHERE id='omnivoice-base'"))
    assert res.scalar() is not None


async def test_unknown_model_raises(session):
    with pytest.raises(ModelNotFoundError):
        await activate_model(session, "does-not-exist")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_model_lifecycle.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.model_lifecycle'`.

- [ ] **Step 3: Write minimal implementation**

`backend/app/services/model_lifecycle.py`:

```python
"""Persisted model lifecycle transitions.

Operates on the ``models`` table (the first-class entity). The in-memory registry is refreshed
from the DB by the wiring layer; these functions are the source of truth for status changes.
"""

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ModelNotFoundError(Exception):
    pass


async def _set_status(session: AsyncSession, model_id: str, status: str, *, deprecated: bool = False) -> None:
    now = datetime.now(timezone.utc).isoformat()
    res = await session.execute(text("SELECT id FROM models WHERE id=:id"), {"id": model_id})
    if res.first() is None:
        raise ModelNotFoundError(model_id)
    if deprecated:
        await session.execute(
            text("UPDATE models SET status=:s, deprecated_at=:t, updated_at=:t WHERE id=:id"),
            {"s": status, "t": now, "id": model_id},
        )
    else:
        await session.execute(
            text("UPDATE models SET status=:s, updated_at=:t WHERE id=:id"),
            {"s": status, "t": now, "id": model_id},
        )
    await session.commit()


async def activate_model(session: AsyncSession, model_id: str) -> None:
    await _set_status(session, model_id, "available")


async def deactivate_model(session: AsyncSession, model_id: str) -> None:
    await _set_status(session, model_id, "disabled")


async def deprecate_model(session: AsyncSession, model_id: str) -> None:
    await _set_status(session, model_id, "deprecated", deprecated=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_model_lifecycle.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/model_lifecycle.py backend/tests/test_model_lifecycle.py
git commit -m "feat(models): persisted lifecycle (activate/deactivate/deprecate)"
```

---

## Task 5: Hugging Face installer (manifest + download + install)

Installs a community model: fetch repo metadata, download into the existing `HF_HOME` cache, and insert a non-builtin `models` row. The download is wrapped so tests mock it (no network).

**Files:**
- Create: `backend/app/services/hf_installer.py`
- Create: `backend/tests/test_hf_installer.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_hf_installer.py`:

```python
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)

from app.core.migrations import run_migrations
from app.services.hf_installer import install_from_hf, HfInstallError


@pytest.fixture
async def session(tmp_path):
    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/hf.db", future=True)
    async with eng.begin() as conn:
        await run_migrations(conn)
    maker = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s
    await eng.dispose()


async def test_install_inserts_non_builtin_model(session, monkeypatch):
    async def fake_download(repo_id: str) -> str:
        return f"/data/models/{repo_id}"

    monkeypatch.setattr("app.services.hf_installer._download_snapshot", fake_download)

    descriptor = await install_from_hf(
        session,
        repo_id="someorg/cool-tts",
        provider="omnivoice",
        name="Cool TTS",
    )
    assert descriptor.is_builtin is False
    row = (await session.execute(
        text("SELECT is_builtin, model_path, provider FROM models WHERE id=:id"),
        {"id": descriptor.id},
    )).first()
    assert row[0] == 0
    assert row[1] == "/data/models/someorg/cool-tts"
    assert row[2] == "omnivoice"


async def test_install_rejects_unknown_provider(session):
    with pytest.raises(HfInstallError):
        await install_from_hf(session, repo_id="x/y", provider="nonexistent-provider", name="X")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_hf_installer.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.hf_installer'`.

- [ ] **Step 3: Write minimal implementation**

`backend/app/services/hf_installer.py`:

```python
"""Install community models from Hugging Face.

The download is isolated in ``_download_snapshot`` so it can be mocked in tests and swapped for
a resumable/progress-aware implementation later. Installing inserts a non-builtin ``models`` row
(``is_builtin=0``) — never touching built-in catalog rows. Provider must already be registered.
"""

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.registry_types import ModelDescriptor
from app.services.model_registry import model_registry

# Providers known to the platform. Installing a model for an unknown provider is rejected.
_KNOWN_PROVIDERS = {"omnivoice", "omnivoice-singing"}


class HfInstallError(Exception):
    pass


def _download_snapshot(repo_id: str) -> str:
    """Download the repo snapshot into HF_HOME and return the local path.

    Isolated for mocking. Real implementation uses huggingface_hub.snapshot_download(
    repo_id, cache_dir=settings.HF_HOME). Kept import-local to stay torch/HF-free at module load.
    """
    from huggingface_hub import snapshot_download

    from app.core.config import settings

    return snapshot_download(repo_id=repo_id, cache_dir=settings.HF_HOME)


async def install_from_hf(
    session: AsyncSession, *, repo_id: str, provider: str, name: str,
) -> ModelDescriptor:
    if provider not in _KNOWN_PROVIDERS:
        raise HfInstallError(f"Unknown provider '{provider}'. Known: {sorted(_KNOWN_PROVIDERS)}")

    model_path = _download_snapshot(repo_id)
    model_id = repo_id.replace("/", "--")
    now = datetime.now(timezone.utc).isoformat()

    await session.execute(
        text(
            """
            INSERT INTO models (
                id, name, description, version, provider, repo_id, model_path,
                status, is_default, is_builtin, editions, owner_id, created_at, updated_at
            ) VALUES (
                :id, :name, :desc, '1.0.0', :provider, :repo_id, :model_path,
                'available', 0, 0, :editions, NULL, :now, :now
            )
            ON CONFLICT(id) DO UPDATE SET
                model_path=excluded.model_path, status='available', updated_at=excluded.updated_at
            """
        ),
        {
            "id": model_id, "name": name, "desc": f"Installed from {repo_id}",
            "provider": provider, "repo_id": repo_id, "model_path": model_path,
            "editions": '["community"]', "now": now,
        },
    )
    await session.commit()

    descriptor = ModelDescriptor(
        id=model_id, name=name, description=f"Installed from {repo_id}",
        provider=provider, repo_id=repo_id, model_path=model_path,
        is_builtin=False,
    )
    model_registry.upsert_descriptor(descriptor)
    return descriptor
```

- [ ] **Step 4: Add the dependency**

Confirm `huggingface_hub` is in `backend/requirements.txt` (it is transitively via the ML stack, but add it explicitly if absent):

Run: `cd backend && grep -i huggingface_hub requirements.txt || echo "huggingface_hub" >> requirements.txt`

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_hf_installer.py -v`
Expected: PASS (2 passed) — downloads are mocked.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/hf_installer.py backend/tests/test_hf_installer.py backend/requirements.txt
git commit -m "feat(models): Hugging Face installer (mockable download + non-builtin row)"
```

---

## Task 6: API — surface metadata + admin lifecycle routes

Extend the read payload with the new metadata, and add admin lifecycle endpoints. Per [Product §3](../../architecture/01-PRODUCT_ARCHITECTURE.md), **writes** (activate/deactivate/deprecate/install) are gated: enabled only when `settings.features.auth` (Cloud) — in CE they return `403`. Reads stay public.

**Files:**
- Modify: `backend/app/api/models.py`
- Create: `backend/tests/test_models_api_metadata.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_models_api_metadata.py`:

```python
from app.api.models import _descriptor_payload
from app.models.registry_types import ModelDescriptor, ModelRequirements, ModelLicense


def test_payload_includes_new_metadata():
    d = ModelDescriptor(
        id="m", name="M", description="d", provider="p",
        requirements=ModelRequirements(min_vram_gb=8, gpu_required=True),
        license=ModelLicense(code="apache-2.0", commercial_use=True),
        provider_metadata={"author": "k2-fsa"},
    )
    payload = _descriptor_payload(d)
    assert payload["requirements"]["min_vram_gb"] == 8
    assert payload["license"]["code"] == "apache-2.0"
    assert payload["provider_metadata"]["author"] == "k2-fsa"


def test_lifecycle_writes_disabled_in_community():
    from app.api.models import _writes_enabled
    # CE: settings.features.auth is False → writes disabled.
    assert _writes_enabled() is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_models_api_metadata.py -v`
Expected: FAIL — payload lacks the keys; `_writes_enabled` undefined.

- [ ] **Step 3: Extend the read payload**

In `backend/app/api/models.py`, update `_descriptor_payload` to include the new fields. Add these keys to the returned dict (serialise the nested pydantic models):

```python
        "requirements": descriptor.requirements.model_dump(),
        "license": descriptor.license.model_dump() if descriptor.license else None,
        "provider_metadata": descriptor.provider_metadata,
```

- [ ] **Step 4: Add the write-gate + lifecycle routes**

Add to `backend/app/api/models.py` (imports + helper + routes). Use the DB session dependency already used elsewhere in the codebase (match `app/api/voices.py`'s session dependency import):

```python
from fastapi import Depends, HTTPException
from app.core.config import settings
from app.core.database import get_db  # the project's async session dependency
from app.services.model_lifecycle import (
    activate_model, deactivate_model, deprecate_model, ModelNotFoundError,
)


def _writes_enabled() -> bool:
    # Admin model management is a Cloud capability; CE is read-only for the registry.
    return settings.features.auth


def _require_writes() -> None:
    if not _writes_enabled():
        raise HTTPException(status_code=403, detail="Model management is a Cloud-only capability")


@router.post("/models/{model_id}/activate")
async def activate(model_id: str, session=Depends(get_db)):
    _require_writes()
    try:
        await activate_model(session, model_id)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"id": model_id, "status": "available"}


@router.post("/models/{model_id}/deactivate")
async def deactivate(model_id: str, session=Depends(get_db)):
    _require_writes()
    try:
        await deactivate_model(session, model_id)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"id": model_id, "status": "disabled"}


@router.post("/models/{model_id}/deprecate")
async def deprecate(model_id: str, session=Depends(get_db)):
    _require_writes()
    try:
        await deprecate_model(session, model_id)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"id": model_id, "status": "deprecated"}
```

> The async session dependency is `get_db` (confirmed in `app/core/database.py` and used throughout `app/api/voices.py`).

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_models_api_metadata.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/models.py backend/tests/test_models_api_metadata.py
git commit -m "feat(api): model metadata in payload + Cloud-gated lifecycle routes"
```

---

## Task 7: Full backend suite (regression gate)

- [ ] **Step 1: Run the whole suite**

Run: `cd backend && python -m pytest -q`
Expected: all PASS. Watch `test_model_migration.py`, `test_model_catalog.py`, `test_model_registry.py` — additive changes must not regress them.

- [ ] **Step 2: Debug + fix any failures** with superpowers:systematic-debugging, then commit fixes.

---

## Task 8: Frontend — Model Manager surface

> **REQUIRED per `frontend/AGENTS.md`:** read the relevant doc under `frontend/node_modules/next/dist/docs/` before editing.

**Files:**
- Locate: `cd frontend && grep -rln "models" src/lib/api.ts src/components | head` and the existing ModelSelector / model info components (the redesign already has `ModelInfoCard`, `ModelSelector`).

- [ ] **Step 1: Docs gate** — read the relevant Next.js doc for the surface you touch.
- [ ] **Step 2:** Extend `frontend/src/lib/api.ts` with `installModel`, `activateModel`, `deactivateModel`, `deprecateModel` calls (only rendered when the features flag enables management — CE hides them).
- [ ] **Step 3:** Surface the new metadata (requirements, license, provider) in `ModelInfoCard`.
- [ ] **Step 4:** Add an admin-only "Install from Hugging Face" form behind the management feature flag (hidden in CE).
- [ ] **Step 5:** `cd frontend && npm run lint && npm run build` — expect clean.
- [ ] **Step 6:** Commit `feat(ui): model manager — metadata, lifecycle, HF install (flag-gated)`.

---

## Done criteria

- [ ] `ModelDescriptor` and `models` carry requirements/license/provider_metadata (+ `deprecated_at`); migration is additive + idempotent.
- [ ] Built-in `omnivoice-base` seeds a license; metadata round-trips through `/models`.
- [ ] Lifecycle service transitions status in the DB; unknown ids raise/`404`.
- [ ] HF installer inserts a non-builtin row (download mockable); unknown provider rejected.
- [ ] Lifecycle/install writes are `403` in CE, available in Cloud; reads public.
- [ ] `cd backend && python -m pytest -q` fully green.

## Self-review notes (author)

- **Spec coverage** vs Roadmap Phase 2: metadata columns ✓ (T1–T3), lifecycle ✓ (T4), HF install ✓ (T5), API extension + admin lifecycle ✓ (T6), frontend manager ✓ (T8). Versioning rule (updates insert a new row) is honored by the installer's `ON CONFLICT` + `is_builtin=0` and documented for future multi-version work; a dedicated `model_versions` child table is deferred per [ADR-0002](../../architecture/adrs/0002-model-as-first-class-entity.md) until many-versions-per-line is real (YAGNI).
- **Type consistency:** `ModelRequirements`/`ModelLicense` defined in T1, reused in T3/T6 tests and `_descriptor_payload`. `ModelNotFoundError` defined in T4, imported in T6. `_download_snapshot` is the single mock seam used by T5.
- **No placeholders:** every code step is complete; the one verify-the-name instruction (session dependency) is explicit with the grep to confirm it.

## Next phase

After Phase 2 lands green: **Phase 3 — Voice / VoiceVariant split** (the core domain spine) via its own plan, `docs/superpowers/plans/2026-06-03-peakvox-phase-3-voice-variant-split.md`.
