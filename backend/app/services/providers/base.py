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
