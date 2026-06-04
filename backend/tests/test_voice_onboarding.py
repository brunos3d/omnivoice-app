from app.services.voice_onboarding import split_profile_row

PROFILE = {
    "id": "uuid-1",
    "public_voice_id": "voice_ABC123",
    "owner_id": "owner-1",
    "name": "Bruno",
    "description": "test",
    "language": "Portuguese",
    "language_code": "pt",
    "transcript": "olá mundo",
    "audio_filename": "voices/uuid-1/reference.wav",
    "characteristics": {"gender": "male"},
    "generation_defaults": {"voice_design": {"gender": "male"}, "num_step": 32},
    "is_public": False,
    "is_favorite": True,
    "status": "ready",
    "usage_count": 5,
}


def test_split_preserves_public_voice_id_on_voice():
    voice, variant = split_profile_row(PROFILE)
    assert voice["public_voice_id"] == "voice_ABC123"
    assert voice["id"] == "uuid-1"  # reuse the profile UUID as the Voice id (stable storage prefix)
    assert voice["name"] == "Bruno"
    assert voice["is_favorite"] is True


def test_split_builds_omnivoice_variant_with_artifacts_and_params():
    voice, variant = split_profile_row(PROFILE)
    assert variant["voice_id"] == "uuid-1"
    assert variant["model_id"] == "omnivoice-base"
    assert variant["artifacts"]["audio"] == "voices/uuid-1/reference.wav"
    assert variant["params"]["transcript"] == "olá mundo"
    assert variant["params"]["generation_defaults"]["num_step"] == 32
    assert variant["source"] == "cloned"
    assert variant["status"] == "ready"
