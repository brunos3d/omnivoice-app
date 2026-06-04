"""Voice onboarding: turn a legacy VoiceProfile into a Voice + OmniVoice VoiceVariant.

``split_profile_row`` is a pure mapping reused by the backfill migration and by runtime
dual-write on voice create/update, so both paths stay identical (ADR-0001 / Migration §2).
"""

from typing import Any

DEFAULT_MODEL_ID = "omnivoice-base"


def split_profile_row(profile: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ``(voice_dict, variant_dict)`` derived from a voice_profiles row.

    The Voice reuses the profile's UUID as its ``id`` (so existing storage prefixes
    ``/data/voices/{id}/`` keep working) and carries ``public_voice_id`` unchanged.
    """
    voice = {
        "id": profile["id"],
        "public_voice_id": profile["public_voice_id"],
        "owner_id": profile.get("owner_id"),
        "creator_id": None,
        "name": profile["name"],
        "description": profile.get("description"),
        "language": profile.get("language"),
        "language_code": profile.get("language_code"),
        "preview_audio": profile.get("audio_filename"),  # the reference doubles as preview initially
        "meta": profile.get("meta"),
        "characteristics": profile.get("characteristics"),
        "royalty_config": None,
        "is_public": bool(profile.get("is_public", False)),
        "is_community_voice": bool(profile.get("is_community_voice", False)),
        "is_preset_voice": bool(profile.get("is_preset_voice", False)),
        "is_favorite": bool(profile.get("is_favorite", False)),
        "status": profile.get("status", "ready"),
        "usage_count": int(profile.get("usage_count", 0) or 0),
    }
    defaults = profile.get("generation_defaults") or {}
    variant = {
        "voice_id": profile["id"],
        "model_id": DEFAULT_MODEL_ID,
        "model_version": None,
        "artifact_type": "reference_sample",
        "artifacts": {"audio": profile.get("audio_filename")},
        "params": {
            "transcript": profile.get("transcript"),
            "voice_design": defaults.get("voice_design"),
            "generation_defaults": defaults,
        },
        "source": "cloned",
        "status": "ready",
    }
    return voice, variant
