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
