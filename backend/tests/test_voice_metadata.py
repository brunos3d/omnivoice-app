from app.services.voice_metadata import (
    characteristics_from_defaults,
    derive_characteristics,
)

CHARACTERISTIC_KEYS = {
    "gender",
    "age_group",
    "accent",
    "pitch",
    "style_tags",
    "speaking_speed",
    "emotional_range",
}


def test_derives_core_attributes_from_voice_design():
    result = derive_characteristics(
        ["male", "young adult", "low pitch", "british accent"]
    )
    assert result["gender"] == "male"
    assert result["age_group"] == "young"
    assert result["pitch"] == "low"
    assert result["accent"] == "british"


def test_returns_all_keys_with_safe_defaults_when_empty():
    result = derive_characteristics([])
    assert set(result.keys()) == CHARACTERISTIC_KEYS
    assert result["gender"] is None
    assert result["age_group"] is None
    assert result["accent"] is None
    assert result["pitch"] is None
    assert result["style_tags"] == []
    assert result["speaking_speed"] is None
    assert result["emotional_range"] is None


def test_handles_none_input():
    result = derive_characteristics(None)
    assert set(result.keys()) == CHARACTERISTIC_KEYS
    assert result["style_tags"] == []


def test_unknown_attributes_are_ignored():
    result = derive_characteristics(["banana", "male", "nonsense"])
    assert result["gender"] == "male"
    assert result["age_group"] is None


def test_style_attribute_becomes_style_tag():
    result = derive_characteristics(["female", "whisper"])
    assert result["gender"] == "female"
    assert "whisper" in result["style_tags"]


def test_speaking_speed_and_emotional_range_from_preset_tags():
    result = derive_characteristics([], preset_tags=["fast", "expressive"])
    assert result["speaking_speed"] == "fast"
    assert result["emotional_range"] == "expressive"


def test_characteristics_from_defaults_extracts_voice_design():
    defaults = {"voice_design": ["male", "british accent"], "num_step": 32}
    result = characteristics_from_defaults(defaults, preset_tags=["fast"], language="English")
    assert result["gender"] == "male"
    assert result["accent"] == "british"
    assert result["speaking_speed"] == "fast"


def test_characteristics_from_defaults_handles_none():
    result = characteristics_from_defaults(None)
    assert result["style_tags"] == []
    assert result["gender"] is None


def test_age_group_normalization():
    assert derive_characteristics(["middle-aged"])["age_group"] == "adult"
    assert derive_characteristics(["elderly"])["age_group"] == "elderly"
    assert derive_characteristics(["child"])["age_group"] == "child"
    assert derive_characteristics(["teenager"])["age_group"] == "teen"
