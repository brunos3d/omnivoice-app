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


from app.services.providers.registry import get_auth_provider, get_billing_provider


def test_community_gets_local_and_null_providers():
    # settings.EDITION defaults to "community"
    assert isinstance(get_auth_provider(), LocalOwnerAuthProvider)
    assert isinstance(get_billing_provider(), NullBillingProvider)
