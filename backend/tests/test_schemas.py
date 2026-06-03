from datetime import datetime, timezone

from app.models.db import VoiceProfile
from app.schemas.voice import VoiceProfileResponse


def test_response_exposes_new_platform_fields():
    now = datetime.now(timezone.utc)
    voice = VoiceProfile(
        id="abc",
        public_voice_id="voice_ABCDE12345",
        owner_id="owner-1",
        name="Narrator",
        language="Portuguese",
        language_code="pt",
        audio_filename="reference.wav",
        preset_tags=["narration"],
        characteristics={"gender": "male", "style_tags": []},
        is_public=False,
        is_community_voice=False,
        is_preset_voice=False,
        is_favorite=True,
        status="ready",
        usage_count=7,
        created_at=now,
        updated_at=now,
    )

    dto = VoiceProfileResponse.model_validate(voice)

    assert dto.public_voice_id == "voice_ABCDE12345"
    assert dto.owner_id == "owner-1"
    assert dto.language_code == "pt"
    assert dto.preset_tags == ["narration"]
    assert dto.characteristics["gender"] == "male"
    assert dto.is_favorite is True
    assert dto.status == "ready"
    assert dto.usage_count == 7
    assert dto.updated_at == now
