# PeakVox Phase 1 — Platform Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the PeakVox foundation — feature flags, schema-ready commercial tables, vendor-neutral provider seams, edition-gated router mounting, and key-prefix groundwork — so every later phase is wiring, not redesign.

**Architecture:** Additive only. New commercial ORM models register on `Base.metadata` and are auto-created by the existing idempotent migration runner (`run_migrations`'s `create_all` step) — empty in CE. A typed `Features` object derived from `settings.EDITION` gates router mounting and (later) service wiring. Auth/billing/payment/payout become abstract interfaces with Null/Local adapters in CE; Clerk/Stripe adapters arrive in later phases. CE behavior is unchanged: all commercial flags off, no new routers mounted.

**Tech Stack:** Python 3.12, FastAPI, async SQLAlchemy + aiosqlite, pydantic-settings, pytest (`asyncio_mode=auto`). Frontend: Next.js 16 / React 19, TypeScript.

**Reference docs:** [Product Architecture](../../architecture/01-PRODUCT_ARCHITECTURE.md) (§4 feature flags, §4.2 deployment boundary), [Data Architecture](../../architecture/03-DATA_ARCHITECTURE.md) (§4 schema-ready tables), [Migration Architecture](../../architecture/08-MIGRATION_ARCHITECTURE.md) (§4, §7).

---

## File Structure

**Create:**
- `backend/app/core/features.py` — the typed `Features` flag set + `for_edition()`.
- `backend/app/core/editions.py` — `mount_cloud_routers(app)` edition-gated mounting helper.
- `backend/app/cloud/__init__.py` — the Cloud-only module boundary (empty package; CE never imports its contents at runtime).
- `backend/app/services/providers/__init__.py`
- `backend/app/services/providers/base.py` — `Principal` + abstract `AuthProvider`, `BillingProvider`, `PaymentProvider`, `PayoutProvider`.
- `backend/app/services/providers/local.py` — CE Null/Local adapters.
- `backend/app/services/providers/registry.py` — `get_auth_provider()` etc., resolved by edition.
- `backend/tests/test_features.py`
- `backend/tests/test_commercial_models.py`
- `backend/tests/test_commercial_migration.py`
- `backend/tests/test_providers.py`
- `backend/tests/test_editions.py`
- `backend/tests/test_api_key_prefix.py`

**Modify:**
- `backend/app/models/db.py` — add `Role`, `Creator`, `MarketplaceListing`, `CreditLedger`, `Transaction`, `Royalty`, `Payout` ORM models.
- `backend/app/core/config.py` — add `features` property; default `APP_NAME` → "PeakVox".
- `backend/app/main.py` — call `mount_cloud_routers(app)`.
- `backend/app/services/api_keys.py` — new `pv_live_` prefix; accept legacy `ov_live_`.
- `frontend/src/` branding + feature-flag-gated nav (Tasks 8–9; exact files located in-task).

**Convention reminders:** string UUID PKs via `_uuid`, `owner_id` for tenancy, JSON columns for flexible attributes, UTC timestamps via `_now`. Migration tests use `create_async_engine` on a `tmp_path` SQLite db and call `run_migrations(conn)` (see `tests/test_model_migration.py`).

---

## Task 1: Feature flags (`Features`)

**Files:**
- Create: `backend/app/core/features.py`
- Create: `backend/tests/test_features.py`
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_features.py`:

```python
from app.core.features import Features


def test_community_disables_all_commercial_features():
    f = Features.for_edition("community")
    assert not any([f.auth, f.tenancy, f.billing, f.marketplace, f.creators, f.payouts])


def test_cloud_enables_ecosystem_features():
    f = Features.for_edition("cloud")
    assert all([f.auth, f.tenancy, f.billing, f.marketplace, f.creators, f.payouts])


def test_enterprise_enables_ecosystem_features():
    f = Features.for_edition("enterprise")
    assert all([f.auth, f.tenancy, f.billing, f.marketplace, f.creators, f.payouts])


def test_unknown_edition_defaults_to_community():
    assert Features.for_edition("banana") == Features.for_edition("community")


def test_settings_exposes_features_for_default_edition():
    from app.core.config import settings
    assert settings.EDITION == "community"
    assert settings.features.marketplace is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_features.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.features'`.

- [ ] **Step 3: Write minimal implementation**

`backend/app/core/features.py`:

```python
"""Edition-derived feature flags.

The single source of truth for which commercial capabilities are active. Flags gate router
mounting and service wiring — never table existence (the schema-ready commercial tables are
always created). Community Edition runs with every commercial flag off.
"""

from dataclasses import dataclass

_CLOUD_EDITIONS = {"cloud", "enterprise"}


@dataclass(frozen=True)
class Features:
    auth: bool = False
    tenancy: bool = False
    billing: bool = False
    marketplace: bool = False
    creators: bool = False
    payouts: bool = False

    @classmethod
    def for_edition(cls, edition: str) -> "Features":
        if edition in _CLOUD_EDITIONS:
            return cls(
                auth=True,
                tenancy=True,
                billing=True,
                marketplace=True,
                creators=True,
                payouts=True,
            )
        return cls()  # community / unknown → all off
```

- [ ] **Step 4: Add the `features` property to Settings**

In `backend/app/core/config.py`, add the import at the top and the property on `Settings` (place the property just before `create_dirs`):

```python
from app.core.features import Features
```

```python
    @property
    def features(self) -> Features:
        return Features.for_edition(self.EDITION)
```

Also change the default app name in the same file:

```python
    APP_NAME: str = "PeakVox"
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_features.py -v`
Expected: PASS (5 passed).

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/features.py backend/app/core/config.py backend/tests/test_features.py
git commit -m "feat(core): edition-derived Features flags + PeakVox app name"
```

---

## Task 2: Schema-ready commercial ORM models

**Files:**
- Modify: `backend/app/models/db.py`
- Create: `backend/tests/test_commercial_models.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_commercial_models.py`:

```python
from app.core.database import Base
import app.models.db  # noqa: F401  (registers tables on Base.metadata)

EXPECTED_TABLES = {
    "roles",
    "creators",
    "marketplace_listings",
    "credit_ledgers",
    "transactions",
    "royalties",
    "payouts",
}


def test_commercial_tables_registered():
    assert EXPECTED_TABLES <= set(Base.metadata.tables.keys())


def test_transactions_has_append_only_shape():
    cols = {c.name for c in Base.metadata.tables["transactions"].columns}
    assert {"id", "owner_id", "type", "amount", "balance_after", "ref", "created_at"} <= cols


def test_royalty_split_columns_present():
    cols = {c.name for c in Base.metadata.tables["royalties"].columns}
    assert {"gross_amount", "creator_amount", "platform_amount", "infra_amount"} <= cols
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_commercial_models.py -v`
Expected: FAIL on `test_commercial_tables_registered` (tables not in metadata).

- [ ] **Step 3: Write minimal implementation**

Append to `backend/app/models/db.py` (after `GenerationJob`). These reuse the module's existing `_uuid`, `_now`, and imported column types:

```python
class Role(Base):
    """Additive role association. CE collapses every role onto the local owner."""

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # user|creator|admin
    scope: Mapped[str | None] = mapped_column(String(36), nullable=True)  # future org id
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Creator(Base):
    """A user's creator identity. Schema-ready; populated only in Cloud."""

    __tablename__ = "creators"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(512), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unverified")
    payout_account_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    royalty_defaults: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class MarketplaceListing(Base):
    """A discovery/pricing wrapper around a Voice. Schema-ready; Cloud-only semantics."""

    __tablename__ = "marketplace_listings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    voice_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    pricing: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    preview_audio: Mapped[str | None] = mapped_column(String(512), nullable=True)
    stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class CreditLedger(Base):
    """Cached per-owner credit balance. Source of truth is the transactions ledger."""

    __tablename__ = "credit_ledgers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class Transaction(Base):
    """Append-only credit ledger. Rows are never updated or deleted — corrections are new rows."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    # purchase | consume | royalty_accrual | payout | adjustment
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # signed credits
    balance_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ref: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Royalty(Base):
    """One royalty-bearing generation's split. Schema-ready; written only in Cloud."""

    __tablename__ = "royalties"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    creator_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    voice_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    generation_job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gross_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    creator_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    platform_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    infra_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="accrued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Payout(Base):
    """A settlement to a creator. Schema-ready; Cloud-only."""

    __tablename__ = "payouts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    creator_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    period: Mapped[str | None] = mapped_column(String(32), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="usd")
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    provider_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_commercial_models.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/db.py backend/tests/test_commercial_models.py
git commit -m "feat(models): schema-ready commercial entities (creators, ledger, royalties, payouts)"
```

---

## Task 3: Migration auto-creates the commercial tables

The runner's step 1 (`Base.metadata.create_all`) already creates every registered table. This task **proves** the new tables are created, stay empty in CE, and that re-running is idempotent — the additive guarantee from [Migration §7](../../architecture/08-MIGRATION_ARCHITECTURE.md).

**Files:**
- Create: `backend/tests/test_commercial_migration.py`
- Modify: `backend/app/core/migrations.py` (only if Step 2 reveals a gap)

- [ ] **Step 1: Write the failing test**

`backend/tests/test_commercial_migration.py`:

```python
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.migrations import run_migrations

COMMERCIAL_TABLES = [
    "roles", "creators", "marketplace_listings",
    "credit_ledgers", "transactions", "royalties", "payouts",
]


@pytest.fixture
async def engine(tmp_path):
    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/commercial.db", future=True)
    yield eng
    await eng.dispose()


async def _table_names(engine):
    async with engine.begin() as conn:
        res = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        return {row[0] for row in res.fetchall()}


async def test_commercial_tables_created(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)
    assert set(COMMERCIAL_TABLES) <= await _table_names(engine)


async def test_commercial_tables_empty_in_community(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)
    async with engine.begin() as conn:
        for table in COMMERCIAL_TABLES:
            res = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            assert res.scalar() == 0, f"{table} should be empty in CE"


async def test_migration_is_idempotent(engine):
    async with engine.begin() as conn:
        await run_migrations(conn)
    async with engine.begin() as conn:
        await run_migrations(conn)  # must not raise
    assert set(COMMERCIAL_TABLES) <= await _table_names(engine)
```

- [ ] **Step 2: Run tests to verify they pass (or fail honestly)**

Run: `cd backend && python -m pytest tests/test_commercial_migration.py -v`
Expected: PASS (3 passed) — because `create_all` already builds the newly-registered tables and seeds nothing into them. If any test FAILS, the runner needs no new DDL (tables auto-create); investigate only the failing assertion. Do not add manual `CREATE TABLE` DDL — that would duplicate `create_all`.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_commercial_migration.py
git commit -m "test(migrations): commercial tables auto-create, stay empty in CE, idempotent"
```

---

## Task 4: Provider seam interfaces + Null/Local adapters

**Files:**
- Create: `backend/app/services/providers/__init__.py` (empty)
- Create: `backend/app/services/providers/base.py`
- Create: `backend/app/services/providers/local.py`
- Create: `backend/tests/test_providers.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_providers.py`:

```python
import pytest

from app.core.config import settings
from app.services.providers.base import (
    AuthProvider, BillingProvider, PaymentProvider, PayoutProvider, Principal,
)
from app.services.providers.local import (
    LocalOwnerAuthProvider, NullBillingProvider, NullPaymentProvider, NullPayoutProvider,
)


async def test_local_owner_resolves_local_principal():
    provider = LocalOwnerAuthProvider()
    principal = await provider.resolve_principal(
        authorization=None, x_api_key=None, session_token=None
    )
    assert isinstance(principal, Principal)
    assert principal.owner_id == settings.LOCAL_OWNER_ID
    assert {"user", "creator", "admin"} <= set(principal.roles)


async def test_null_billing_is_disabled():
    with pytest.raises(NotImplementedError):
        await NullBillingProvider().purchase_credits(owner_id="x", amount=100)


async def test_adapters_satisfy_interfaces():
    assert isinstance(LocalOwnerAuthProvider(), AuthProvider)
    assert isinstance(NullBillingProvider(), BillingProvider)
    assert isinstance(NullPaymentProvider(), PaymentProvider)
    assert isinstance(NullPayoutProvider(), PayoutProvider)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_providers.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.providers'`.

- [ ] **Step 3: Write the interfaces**

`backend/app/services/providers/__init__.py`: empty file.

`backend/app/services/providers/base.py`:

```python
"""Vendor-neutral seams for identity, billing, payments, and payouts.

CE wires the Local/Null adapters in ``local.py``; Cloud wires Clerk/Stripe adapters in later
phases. Call sites depend only on these interfaces — adding a vendor is adding an adapter, not
a domain change (mirrors the existing ``core/identity.get_current_owner_id`` seam).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Principal:
    owner_id: str
    org_id: str | None = None
    roles: tuple[str, ...] = field(default_factory=tuple)
    plan: str | None = None


class AuthProvider(ABC):
    @abstractmethod
    async def resolve_principal(
        self, *, authorization: str | None, x_api_key: str | None, session_token: str | None
    ) -> Principal | None: ...


class BillingProvider(ABC):
    @abstractmethod
    async def purchase_credits(self, *, owner_id: str, amount: int) -> str: ...


class PaymentProvider(ABC):
    @abstractmethod
    async def charge(self, *, owner_id: str, amount: int, currency: str) -> str: ...


class PayoutProvider(ABC):
    @abstractmethod
    async def transfer(self, *, account_ref: str, amount: int, currency: str) -> str: ...
```

- [ ] **Step 4: Write the Local/Null adapters**

`backend/app/services/providers/local.py`:

```python
"""Community Edition adapters: a local-owner identity and disabled monetization."""

from app.core.config import settings
from app.services.providers.base import (
    AuthProvider, BillingProvider, PaymentProvider, PayoutProvider, Principal,
)

_LOCAL_ROLES = ("user", "creator", "admin")


class LocalOwnerAuthProvider(AuthProvider):
    """Every request resolves to the single seeded local owner with all roles."""

    async def resolve_principal(self, *, authorization=None, x_api_key=None, session_token=None) -> Principal:
        return Principal(owner_id=settings.LOCAL_OWNER_ID, roles=_LOCAL_ROLES)


class _Disabled:
    _feature = "feature"

    def _fail(self):
        raise NotImplementedError(f"{self._feature} is a Cloud-only feature (disabled in Community Edition)")


class NullBillingProvider(_Disabled, BillingProvider):
    _feature = "Billing"

    async def purchase_credits(self, *, owner_id: str, amount: int) -> str:
        self._fail()


class NullPaymentProvider(_Disabled, PaymentProvider):
    _feature = "Payments"

    async def charge(self, *, owner_id: str, amount: int, currency: str) -> str:
        self._fail()


class NullPayoutProvider(_Disabled, PayoutProvider):
    _feature = "Payouts"

    async def transfer(self, *, account_ref: str, amount: int, currency: str) -> str:
        self._fail()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_providers.py -v`
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/providers backend/tests/test_providers.py
git commit -m "feat(providers): vendor-neutral auth/billing/payment/payout seams + CE adapters"
```

---

## Task 5: Provider registry resolved by edition

**Files:**
- Create: `backend/app/services/providers/registry.py`
- Modify: `backend/tests/test_providers.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_providers.py`:

```python
from app.services.providers.registry import get_auth_provider, get_billing_provider


def test_community_gets_local_and_null_providers():
    # settings.EDITION defaults to "community"
    assert isinstance(get_auth_provider(), LocalOwnerAuthProvider)
    assert isinstance(get_billing_provider(), NullBillingProvider)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_providers.py::test_community_gets_local_and_null_providers -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.providers.registry'`.

- [ ] **Step 3: Write minimal implementation**

`backend/app/services/providers/registry.py`:

```python
"""Resolve the active provider adapter for the current edition.

CE → Local/Null adapters. Cloud phases register Clerk/Stripe adapters here (Phases 4–6) behind
``settings.features`` without changing any call site.
"""

from functools import lru_cache

from app.core.config import settings
from app.services.providers.base import (
    AuthProvider, BillingProvider, PaymentProvider, PayoutProvider,
)
from app.services.providers.local import (
    LocalOwnerAuthProvider, NullBillingProvider, NullPaymentProvider, NullPayoutProvider,
)


@lru_cache
def get_auth_provider() -> AuthProvider:
    # Cloud adapter (ClerkAuthProvider) is wired in Phase 4 when settings.features.auth is True.
    return LocalOwnerAuthProvider()


@lru_cache
def get_billing_provider() -> BillingProvider:
    return NullBillingProvider()


@lru_cache
def get_payment_provider() -> PaymentProvider:
    return NullPaymentProvider()


@lru_cache
def get_payout_provider() -> PayoutProvider:
    return NullPayoutProvider()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_providers.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/providers/registry.py backend/tests/test_providers.py
git commit -m "feat(providers): edition-resolved provider registry"
```

---

## Task 6: Edition-gated router mounting + Cloud module boundary

**Files:**
- Create: `backend/app/cloud/__init__.py`
- Create: `backend/app/core/editions.py`
- Create: `backend/tests/test_editions.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_editions.py`:

```python
from fastapi import FastAPI

from app.core.editions import mount_cloud_routers
from app.core.features import Features


def _paths(app: FastAPI) -> set[str]:
    return {r.path for r in app.routes}


def test_community_mounts_no_cloud_routers():
    app = FastAPI()
    before = _paths(app)
    mount_cloud_routers(app, features=Features.for_edition("community"))
    assert _paths(app) == before  # nothing added in CE


def test_cloud_features_allow_mounting_hook():
    # With cloud features, the hook runs without error (concrete routers arrive in later phases).
    app = FastAPI()
    mount_cloud_routers(app, features=Features.for_edition("cloud"))
    # No cloud routers exist yet, so still no new paths — but the call path is exercised.
    assert isinstance(_paths(app), set)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_editions.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.editions'`.

- [ ] **Step 3: Create the Cloud boundary package**

`backend/app/cloud/__init__.py`:

```python
"""PeakVox Cloud-only modules (ecosystem layer).

Nothing here is imported by Community Edition at runtime. Cloud routers (billing, marketplace
publishing, creator console, metering) are added in later phases and mounted exclusively via
``app.core.editions.mount_cloud_routers`` when the corresponding feature flag is on.
"""
```

- [ ] **Step 4: Write the mounting helper**

`backend/app/core/editions.py`:

```python
"""Edition-gated router mounting.

Cloud routers mount only when their feature flag is on. In Community Edition this is a no-op,
keeping the commercial surface entirely unmounted (not merely 404) — the open-core deployment
boundary from docs/architecture/01-PRODUCT_ARCHITECTURE.md §4.2.
"""

import logging

from fastapi import FastAPI

from app.core.features import Features

logger = logging.getLogger(__name__)


def mount_cloud_routers(app: FastAPI, *, features: Features) -> None:
    """Mount Cloud-only routers gated by feature flags. No-op in Community Edition.

    Later phases add blocks like:

        if features.billing:
            from app.cloud.billing import router as billing_router
            app.include_router(billing_router, prefix="/billing", tags=["Billing"])
    """
    if not any(
        [features.auth, features.billing, features.marketplace, features.creators, features.payouts]
    ):
        return  # Community Edition: mount nothing.
    logger.info("Cloud edition detected — mounting enabled cloud routers")
    # Phase 4+ register concrete routers here, each guarded by its flag.
```

- [ ] **Step 5: Wire it into the app**

In `backend/app/main.py`, add the import near the other `app.core` imports:

```python
from app.core.editions import mount_cloud_routers
```

and add this line at the end of the file, after the last `app.include_router(...)`:

```python
mount_cloud_routers(app, features=settings.features)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_editions.py -v`
Expected: PASS (2 passed).

- [ ] **Step 7: Commit**

```bash
git add backend/app/cloud backend/app/core/editions.py backend/app/main.py backend/tests/test_editions.py
git commit -m "feat(editions): cloud module boundary + edition-gated router mounting"
```

---

## Task 7: API key prefix `pv_live_` (accept legacy `ov_live_`)

**Files:**
- Modify: `backend/app/services/api_keys.py`
- Create: `backend/tests/test_api_key_prefix.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_api_key_prefix.py`:

```python
from app.services.api_keys import (
    KEY_PREFIX, LEGACY_KEY_PREFIX, generate_api_key, is_known_key,
)


def test_new_keys_use_pv_prefix():
    raw, display, _hash = generate_api_key()
    assert KEY_PREFIX == "pv_live_"
    assert raw.startswith("pv_live_")
    assert display.startswith("pv_live_")


def test_legacy_prefix_still_recognized():
    assert LEGACY_KEY_PREFIX == "ov_live_"
    assert is_known_key("pv_live_abc123") is True
    assert is_known_key("ov_live_abc123") is True
    assert is_known_key("nope_abc123") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_api_key_prefix.py -v`
Expected: FAIL with `ImportError: cannot import name 'LEGACY_KEY_PREFIX'`.

- [ ] **Step 3: Update the key service**

In `backend/app/services/api_keys.py`, change the prefix constants near the top:

```python
KEY_PREFIX = "pv_live_"
LEGACY_KEY_PREFIX = "ov_live_"
_SECRET_BYTES = 24  # → 48 hex chars after the prefix
_DISPLAY_PREFIX_LEN = len(KEY_PREFIX) + 8
```

Add a recognizer helper (place it just after `hash_key`):

```python
def is_known_key(raw_key: str) -> bool:
    """True if the key carries a recognised prefix (current or legacy)."""
    return bool(raw_key) and (
        raw_key.startswith(KEY_PREFIX) or raw_key.startswith(LEGACY_KEY_PREFIX)
    )
```

Update the guard in `verify_api_key` to accept both prefixes — replace:

```python
    if not raw_key or not raw_key.startswith(KEY_PREFIX):
        return None
```

with:

```python
    if not is_known_key(raw_key):
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_api_key_prefix.py tests/test_api_keys.py -v`
Expected: PASS (existing `test_api_keys.py` still green; new file passes). If `test_api_keys.py` hard-codes `ov_live_`, update those assertions to `pv_live_` in the same commit (legacy keys remain verifiable via `is_known_key`).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/api_keys.py backend/tests/test_api_key_prefix.py backend/tests/test_api_keys.py
git commit -m "feat(api-keys): mint pv_live_ keys; keep verifying legacy ov_live_ keys"
```

---

## Task 8: Run the full backend suite (regression gate)

- [ ] **Step 1: Run the whole suite**

Run: `cd backend && python -m pytest -q`
Expected: all tests PASS — the new tables/flags/seams are additive and must not regress existing voice/model/migration/api-key tests.

- [ ] **Step 2: If anything fails**

Use superpowers:systematic-debugging. The most likely breakage is an existing test asserting `APP_NAME == "OmniVoice Platform"` or an `ov_live_` literal — update those assertions to the new values (PeakVox / `pv_live_`), since the legacy key path stays supported via `is_known_key`.

- [ ] **Step 3: Commit any test fixes**

```bash
git add backend/tests
git commit -m "test: align existing tests with PeakVox name and pv_ key prefix"
```

---

## Task 9: Frontend — PeakVox branding + feature-flag-gated nav

> **REQUIRED per `frontend/AGENTS.md`:** Before any Next.js work, read the relevant doc under `frontend/node_modules/next/dist/docs/`. Treat training data as outdated.

**Files:**
- Locate first: `cd frontend && grep -rl "OmniVoice" src/ | head` and `grep -rn "nav\|Nav\|sidebar\|Sidebar" src/app src/components | head` to find the brand string(s) and the navigation component.
- Modify: the located brand/title file(s) and the located nav component.
- Modify: `frontend/src/lib/api.ts` (add a features fetch) and `frontend/package.json` (`name` field if it reads `omnivoice`).

- [ ] **Step 1: Read the Next.js docs gate**

Run: `ls frontend/node_modules/next/dist/docs/` and read the doc relevant to the file you'll touch (e.g. app-router metadata for the title/brand, or components for the nav). Confirm the current API before editing.

- [ ] **Step 2: Rebrand the visible product name**

Replace user-facing "OmniVoice" / "OmniVoice Platform" strings with "PeakVox" in the located brand/title/metadata files (page `<title>`, header/logo text, README-driven UI copy). Do **not** rename the `omnivoice-base` model id or the `omnivoice` storage bucket — those are model/infra identifiers, not the product name (see [Migration §3](../../architecture/08-MIGRATION_ARCHITECTURE.md)).

- [ ] **Step 3: Expose edition features to the frontend**

Add a backend read-only endpoint that returns the active flags (extend `backend/app/api/settings.py`): a `GET` returning `settings.features` as JSON (`{ "marketplace": false, "creators": false, ... }`). Add a backend test asserting CE returns all-false. Then in `frontend/src/lib/api.ts` add a `getFeatures()` call.

- [ ] **Step 4: Gate commercial nav items**

In the located nav component, render marketplace/creator/billing entries only when the corresponding feature flag is true. In CE (all false) these never render — matching the backend's unmounted routers. Keep core nav (Studio/TTS, Voices, Models, API keys) always visible.

- [ ] **Step 5: Verify the build**

Run: `cd frontend && npm run lint && npm run build`
Expected: lint clean, build succeeds. Verify in the running app (see the `run` skill) that CE shows no marketplace/creator/billing nav and the product reads "PeakVox".

- [ ] **Step 6: Commit**

```bash
git add frontend
git commit -m "feat(ui): PeakVox branding + feature-flag-gated commercial nav"
```

---

## Done criteria

- [ ] `settings.features` is the single source of truth; CE = all commercial flags off.
- [ ] The seven commercial tables exist (auto-created), are empty in CE, and migration is idempotent.
- [ ] Auth/billing/payment/payout exist as interfaces with CE Local/Null adapters, resolved by edition.
- [ ] Cloud routers mount only under cloud features; CE mounts none (`app/cloud/` boundary in place).
- [ ] New API keys are `pv_live_`; legacy `ov_live_` keys still verify.
- [ ] Frontend reads "PeakVox" and hides commercial nav in CE.
- [ ] `cd backend && python -m pytest -q` is fully green.

## Self-review notes (author)

- **Spec coverage** vs Roadmap Phase 1: feature flags ✓ (T1), schema-ready tables ✓ (T2–T3), vendor seams ✓ (T4–T5), edition-gated mounting + `app/cloud` boundary ✓ (T6), branding ✓ (T9), `pv_`/`ov_` keys ✓ (T7). Frontend nav gating ✓ (T9).
- **Type consistency:** `Features` fields (`auth, tenancy, billing, marketplace, creators, payouts`) are identical across T1/T5/T6. `Principal(owner_id, org_id, roles, plan)` is defined once (T4) and reused (T5). Key constants `KEY_PREFIX`/`LEGACY_KEY_PREFIX`/`is_known_key` defined in T7 and used by its tests.
- **No placeholders:** every code step shows complete code; the only deliberately-deferred work (concrete cloud routers / Clerk / Stripe adapters) is explicitly Phase 4–6 and marked as such in comments, not as TODOs in this phase's deliverable.

## Next phases

After this lands and the suite is green: **Phase 2 (Model Registry hardening)** then **Phase 3 (Voice/VoiceVariant split)** each get their own plan via the writing-plans skill, in that order (the critical path from [Roadmap §cross-phase order](../../architecture/09-ROADMAP.md)).
