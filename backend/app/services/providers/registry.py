"""Resolve the active provider adapter for the current edition.

CE → Local/Null adapters. Cloud phases register Clerk/Stripe adapters here (Phases 4–6) behind
``settings.features`` without changing any call site.
"""

from functools import lru_cache

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
