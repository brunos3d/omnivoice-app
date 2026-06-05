from typing import Optional
from pydantic import BaseModel


class ProviderVoiceResponse(BaseModel):
    provider_voice_id: str
    provider_id: str
    external_id: str
    name: str
    description: str = ""
    language: Optional[str] = None
    gender: Optional[str] = None
    is_default: bool = False
