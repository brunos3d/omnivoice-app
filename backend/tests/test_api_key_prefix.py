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
