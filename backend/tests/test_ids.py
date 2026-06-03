from app.utils.ids import (
    VOICE_ID_PREFIX,
    generate_public_voice_id,
    generate_unique_public_voice_id,
)

# Crockford base32 deliberately excludes these visually ambiguous letters.
_EXCLUDED = set("ILOU")


def test_public_voice_id_has_prefix_and_length():
    vid = generate_public_voice_id()
    assert vid.startswith(VOICE_ID_PREFIX)
    body = vid[len(VOICE_ID_PREFIX):]
    assert len(body) == 10


def test_public_voice_id_uses_crockford_alphabet_only():
    body = generate_public_voice_id()[len(VOICE_ID_PREFIX):]
    assert _EXCLUDED.isdisjoint(set(body))
    assert body.isupper() or body.isdigit() or all(c.isalnum() for c in body)
    for c in body:
        assert c in "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def test_public_voice_ids_are_random():
    ids = {generate_public_voice_id() for _ in range(50)}
    # Vanishingly small chance of a collision across 50 draws of 32^10 space.
    assert len(ids) == 50


def test_unique_generator_retries_on_collision():
    taken = {"voice_AAAAAAAAAA"}
    sequence = iter(["voice_AAAAAAAAAA", "voice_BBBBBBBBBB"])

    vid = generate_unique_public_voice_id(
        exists=lambda v: v in taken,
        _gen=lambda: next(sequence),
    )

    assert vid == "voice_BBBBBBBBBB"
