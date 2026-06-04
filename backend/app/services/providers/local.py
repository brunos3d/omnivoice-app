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
