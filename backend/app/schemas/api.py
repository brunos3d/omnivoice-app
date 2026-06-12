"""Schemas for API-key management and the public `/api/v1` surface.

The public API intentionally uses camelCase field names (voiceId, languageCode, …) to
match common SDK/REST conventions and the brief's examples, independent of the internal
snake_case models.
"""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ── API key management (internal dashboard) ──────────────────────────────────
class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    prefix: str
    status: str
    created_at: datetime
    last_used_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ApiKeyCreateResponse(ApiKeyResponse):
    """Returned only at creation — carries the raw key exactly once."""

    key: str


# ── Public /api/v1 voice resources ───────────────────────────────────────────
class V1Voice(BaseModel):
    voiceId: str
    name: str
    language: Optional[str] = None


class V1VoiceDetail(V1Voice):
    languageCode: Optional[str] = None
    description: Optional[str] = None
    usageCount: int = 0
    characteristics: Optional[dict[str, Any]] = None
    createdAt: datetime


class V1VoiceList(BaseModel):
    voices: list[V1Voice]
    nextCursor: Optional[str] = None


# ── Public /api/v1 model + RuntimeVariant discovery (ADR-0020) ───────────────
# Model-agnostic, public-safe projections. Capabilities are exposed with their
# canonical snake_case ``supports_*`` names (ADR-0003 vocabulary), matching the
# capability contract and the developer-facing examples. No model internals
# (repo ids, model paths, checkpoint refs/formats/digests) ever appear here.
class V1RuntimeVariant(BaseModel):
    """A public RuntimeVariant (model variation: base / singing / pt-br …).

    NOTE: this is a RuntimeVariant (ADR-0018), never a VoiceVariant — the latter
    is a voice's internal realization and is never exposed publicly (ADR-0004 §6).
    """

    variantId: str
    name: str
    description: Optional[str] = None
    isDefault: bool = False
    trust: Optional[str] = None
    capabilities: list[str] = Field(default_factory=list)
    sourceType: Optional[str] = None


class V1Model(BaseModel):
    modelId: str
    name: str
    description: Optional[str] = None
    isDefault: bool = False
    languages: list[str] = Field(default_factory=list)
    defaultVariantId: Optional[str] = None


class V1ModelDetail(V1Model):
    capabilities: dict[str, Any] = Field(default_factory=dict)
    settingsSchema: Optional[dict[str, Any]] = None
    variants: list[V1RuntimeVariant] = Field(default_factory=list)


class V1ModelList(BaseModel):
    models: list[V1Model]


class V1Capabilities(BaseModel):
    modelId: str
    capabilities: dict[str, Any] = Field(default_factory=dict)


class V1VariantList(BaseModel):
    modelId: str
    variants: list[V1RuntimeVariant]


class V1CompatibleModels(BaseModel):
    voiceId: str
    models: list[V1Model]


class V1CompatibleVariants(BaseModel):
    voiceId: str
    modelId: Optional[str] = None
    variants: list[V1RuntimeVariant]


class TextToSpeechRequest(BaseModel):
    voiceId: str
    text: str = Field(..., min_length=1)
    modelId: Optional[str] = None
    # RuntimeVariant id (ADR-0018), e.g. "base"/"singing". Omitted → model default.
    variantId: Optional[str] = None
    language: Optional[str] = None
    format: Literal["wav", "mp3"] = "wav"
    # Platform-level, capability-gated overrides (validated against the model's
    # declared settings schema when present). E.g. {"speed": 1.1}.
    generationSettings: Optional[dict[str, Any]] = None
    # Model-specific pass-through. Deliberately untyped so adding a model
    # parameter never changes the public API. E.g. {"cfg_scale": 2.0}.
    providerSettings: Optional[dict[str, Any]] = None


class TextToSpeechUrlResponse(BaseModel):
    """Returned when the caller requests a download URL instead of a stream."""

    jobId: str
    audioUrl: str
    format: str
    durationSeconds: Optional[float] = None
