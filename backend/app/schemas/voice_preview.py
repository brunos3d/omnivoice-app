from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class VoicePreviewResponse(BaseModel):
    id: str
    voice_id: str
    preview_origin: str  # "reference" | "provider" | "generated" | "user" | "marketplace"
    language: Optional[str] = None
    source_model_id: Optional[str] = None
    storage_key: str
    duration: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VoicePreviewList(BaseModel):
    items: list[VoicePreviewResponse]


class VoicePreviewCreate(BaseModel):
    preview_origin: str
    language: Optional[str] = None
    source_model_id: Optional[str] = None
    storage_key: str
    duration: Optional[float] = None
