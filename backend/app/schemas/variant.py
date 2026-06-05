from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class VariantBuildResponse(BaseModel):
    voice_id: str
    model_id: str
    status: str
    active_artifact_version: Optional[int] = None


class VariantStatusResponse(BaseModel):
    model_id: str
    model_name: str
    status: str
    active_artifact_version: Optional[int] = None
    artifact_count: int = 0
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class VariantListItem(BaseModel):
    model_id: str
    model_name: str
    status: str
    active_artifact_version: Optional[int] = None


class ArtifactVersionResponse(BaseModel):
    version: int
    created_at: datetime
    is_active: bool
    model_version: Optional[str] = None
    size_bytes: Optional[int] = None
    storage_keys: Optional[dict[str, Any]] = None
