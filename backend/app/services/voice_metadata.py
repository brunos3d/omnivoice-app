"""Derivation of the denormalized ``characteristics`` snapshot.

``voice_design`` (the structured attributes chosen in the Voice Design Builder) is the
single source of truth. ``characteristics`` is a derived, read-only snapshot that
filtering / search / pagination / recommendations read instead of recomputing.

Any change to ``voice_design`` must regenerate the snapshot via this function — there
is no manual editing of ``characteristics``.

The category membership below mirrors the controlled vocabulary in
``frontend/src/config/voice-design.ts``. Both ultimately reference the OmniVoice
voice-design spec.
"""

from typing import Optional

_GENDER_VALUES = {"male", "female"}

_AGE_MAP = {
    "child": "child",
    "teenager": "teen",
    "young adult": "young",
    "middle-aged": "adult",
    "elderly": "elderly",
}

_PITCH_VALUES = {
    "very low pitch",
    "low pitch",
    "moderate pitch",
    "high pitch",
    "very high pitch",
}

_STYLE_VALUES = {"whisper"}

# Free-text preset-tag keywords that map onto narrative characteristics.
_SPEED_KEYWORDS = {"slow", "fast", "normal"}
_EMOTION_KEYWORDS = {"expressive", "neutral", "monotone", "wide", "narrow"}

CHARACTERISTIC_KEYS = (
    "gender",
    "age_group",
    "accent",
    "pitch",
    "style_tags",
    "speaking_speed",
    "emotional_range",
)


def derive_characteristics(
    voice_design: Optional[list[str]],
    preset_tags: Optional[list[str]] = None,
    language: Optional[str] = None,  # noqa: ARG001 — reserved for future derivation
) -> dict:
    """Build the characteristics snapshot from voice_design + preset tags.

    Unknown attributes are ignored (their fields stay ``None``). The result always
    contains every key in :data:`CHARACTERISTIC_KEYS`.
    """
    design = voice_design or []
    tags = [t.lower() for t in (preset_tags or [])]

    gender = next((v for v in design if v in _GENDER_VALUES), None)
    age_group = next((_AGE_MAP[v] for v in design if v in _AGE_MAP), None)
    pitch = next(
        (v.removesuffix(" pitch") for v in design if v in _PITCH_VALUES), None
    )
    accent = next(
        (v.removesuffix(" accent") for v in design if v.endswith(" accent")), None
    )
    style_tags = [v for v in design if v in _STYLE_VALUES]

    speaking_speed = next((t for t in tags if t in _SPEED_KEYWORDS), None)
    emotional_range = next((t for t in tags if t in _EMOTION_KEYWORDS), None)

    return {
        "gender": gender,
        "age_group": age_group,
        "accent": accent,
        "pitch": pitch,
        "style_tags": style_tags,
        "speaking_speed": speaking_speed,
        "emotional_range": emotional_range,
    }


def characteristics_from_defaults(
    generation_defaults: Optional[dict],
    preset_tags: Optional[list[str]] = None,
    language: Optional[str] = None,
) -> dict:
    """Derive characteristics from a generation_defaults dict.

    ``voice_design`` lives inside generation_defaults; this convenience wrapper pulls it
    out so callers (create/update/save-defaults endpoints) can regenerate the snapshot
    whenever voice_design changes.
    """
    voice_design = (generation_defaults or {}).get("voice_design") or []
    return derive_characteristics(voice_design, preset_tags=preset_tags, language=language)
