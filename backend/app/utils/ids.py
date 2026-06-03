"""Stable public identifier generation.

The public_voice_id is the external contract for voices (APIs, SDKs, Copy-Voice-ID,
community voices, import/export, cloud sync). It is generated once and never changes.
"""

import secrets
from typing import Callable

VOICE_ID_PREFIX = "voice_"

# Crockford base32 — excludes I, L, O, U to avoid visual ambiguity.
CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

_BODY_LENGTH = 10


def generate_public_voice_id() -> str:
    """Return a new, random public voice id, e.g. ``voice_8JXQ29K4L3``."""
    body = "".join(secrets.choice(CROCKFORD_ALPHABET) for _ in range(_BODY_LENGTH))
    return f"{VOICE_ID_PREFIX}{body}"


def generate_unique_public_voice_id(
    exists: Callable[[str], bool],
    _gen: Callable[[], str] = generate_public_voice_id,
) -> str:
    """Generate a public voice id that is not already taken.

    ``exists`` returns True when a candidate id is already in use. Collisions in a
    32^10 space are vanishingly rare, but we retry to be correct.
    """
    while True:
        candidate = _gen()
        if not exists(candidate):
            return candidate
