"""Public REST API (`/api/v1`).

Authenticated with an API key (``Authorization: Bearer ov_live_…`` or ``X-API-Key``).
Voices are addressed externally by their stable ``public_voice_id``. Endpoints reuse the
existing voice + generation services so behavior matches the app exactly.
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.db import ApiKey, GenerationJob, VoiceProfile
from app.core.config import settings as app_settings
from app.schemas.api import (
    TextToSpeechRequest,
    TextToSpeechUrlResponse,
    V1Capabilities,
    V1CompatibleModels,
    V1CompatibleVariants,
    V1Model,
    V1ModelDetail,
    V1ModelList,
    V1RuntimeVariant,
    V1VariantList,
    V1Voice,
    V1VoiceDetail,
    V1VoiceList,
)
from app.services.api_keys import extract_api_token, verify_api_key
from app.services.storage import storage
from app.services.model_registry import model_registry
from app.services.runtime import runtime as peakvox_runtime
from app.services.voice_metadata import characteristics_from_defaults
from app.services.voice_repository import get_voice_by_public_id, list_voices_page
from app.utils.streaming import stream_object
from app.api.voices import _process_and_upload, resolve_voice_audio_key
from app.api.generation import AUDIO_FORMATS, _ensure_format, _process_job

logger = logging.getLogger(__name__)
router = APIRouter()

# Public API enforces a shorter reference-audio limit than the app.
PUBLIC_REF_AUDIO_LIMIT_S = 10.0


async def enforce_rate_limit(key: ApiKey) -> None:
    """Rate-limit hook (no-op in Community Edition).

    Cloud/Enterprise editions plug a real limiter (per-key quotas, token buckets) here
    without touching call sites.
    """
    return None


async def require_api_key(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    """Authenticate the request via API key, returning the key record."""
    token = extract_api_token(authorization, x_api_key)
    if not token:
        raise HTTPException(status_code=401, detail="Missing API key")
    key = await verify_api_key(db, token)
    if key is None:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    await enforce_rate_limit(key)
    return key


def _to_detail(voice: VoiceProfile) -> V1VoiceDetail:
    return V1VoiceDetail(
        voiceId=voice.public_voice_id,
        name=voice.name,
        language=voice.language,
        languageCode=voice.language_code,
        description=voice.description,
        usageCount=voice.usage_count,
        characteristics=voice.characteristics,
        createdAt=voice.created_at,
    )


# ── Public projections (ADR-0020) ────────────────────────────────────────────
# Model-agnostic, public-safe. RuntimeVariants are exposed without checkpoint
# internals (no source_ref/format/digest), mirroring the composed view's
# discipline (ADR-0004 §6). VoiceVariants are NEVER exposed here.


def _runtime_variants_for_model(model_id: str) -> list[V1RuntimeVariant]:
    """Public RuntimeVariants offered for a model, across its runtimes.

    Returns an empty list when the runtime subsystem is not wired (the implicit
    'base' variant is then represented by the model's ``defaultVariantId``).
    """
    manager = getattr(peakvox_runtime, "_runtime_manager", None)
    if manager is None:
        return []
    out: list[V1RuntimeVariant] = []
    seen: set[str] = set()
    for desc in manager.registry.list_for_model(model_id):
        for v in manager.registry.list_variants_for_runtime(desc.metadata.id):
            if v.spec.model_binding.model_id != model_id or v.metadata.id in seen:
                continue
            seen.add(v.metadata.id)
            out.append(
                V1RuntimeVariant(
                    variantId=v.metadata.id,
                    name=v.metadata.name,
                    description=v.metadata.description,
                    isDefault=v.spec.is_default,
                    trust=v.metadata.trust,
                    capabilities=list(v.spec.capabilities),
                    sourceType=v.spec.checkpoint.source_type,
                )
            )
    out.sort(key=lambda d: (not d.isDefault, d.variantId))
    return out


def _default_variant_id(model_id: str, variants: Optional[list[V1RuntimeVariant]] = None) -> Optional[str]:
    variants = variants if variants is not None else _runtime_variants_for_model(model_id)
    for v in variants:
        if v.isDefault:
            return v.variantId
    return variants[0].variantId if variants else None


def _model_summary(descriptor, default_variant_id: Optional[str] = None) -> V1Model:
    return V1Model(
        modelId=descriptor.id,
        name=descriptor.name,
        description=descriptor.description,
        isDefault=descriptor.is_default,
        languages=descriptor.supported_languages,
        defaultVariantId=default_variant_id if default_variant_id is not None else _default_variant_id(descriptor.id),
    )


def _get_public_model_or_404(model_id: str):
    """Resolve a model that is available in the current edition, else 404."""
    descriptor = model_registry.get(model_id)
    if descriptor is None or app_settings.EDITION not in descriptor.editions:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return descriptor


@router.get("/models", response_model=V1ModelList, summary="List models")
async def v1_list_models(_key: ApiKey = Depends(require_api_key)):
    """List models available in this edition. Use a ``modelId`` with TTS to select one."""
    models = model_registry.list_models(edition=app_settings.EDITION)
    return V1ModelList(models=[_model_summary(m) for m in models])


@router.get("/models/{model_id}", response_model=V1ModelDetail, summary="Get a model")
async def v1_get_model(model_id: str, _key: ApiKey = Depends(require_api_key)):
    """A model's public metadata: capabilities, declared settings schema, and RuntimeVariants."""
    descriptor = _get_public_model_or_404(model_id)
    variants = _runtime_variants_for_model(descriptor.id)
    settings_schema = descriptor.settings_schema.model_dump() if descriptor.settings_schema else None
    return V1ModelDetail(
        modelId=descriptor.id,
        name=descriptor.name,
        description=descriptor.description,
        isDefault=descriptor.is_default,
        languages=descriptor.supported_languages,
        defaultVariantId=_default_variant_id(descriptor.id, variants),
        capabilities=descriptor.capabilities.model_dump(),
        settingsSchema=settings_schema,
        variants=variants,
    )


@router.get(
    "/models/{model_id}/capabilities",
    response_model=V1Capabilities,
    summary="Get a model's capabilities",
)
async def v1_get_model_capabilities(model_id: str, _key: ApiKey = Depends(require_api_key)):
    """The model's declared capability contract (ADR-0003). Branch on these, not on model id."""
    descriptor = _get_public_model_or_404(model_id)
    return V1Capabilities(modelId=descriptor.id, capabilities=descriptor.capabilities.model_dump())


@router.get(
    "/models/{model_id}/variants",
    response_model=V1VariantList,
    summary="List a model's RuntimeVariants",
)
async def v1_list_model_variants(model_id: str, _key: ApiKey = Depends(require_api_key)):
    """RuntimeVariants (base / singing / pt-br …) for a model. Pass ``variantId`` to TTS."""
    descriptor = _get_public_model_or_404(model_id)
    return V1VariantList(modelId=descriptor.id, variants=_runtime_variants_for_model(descriptor.id))


@router.get(
    "/models/{model_id}/variants/{variant_id}",
    response_model=V1RuntimeVariant,
    summary="Get a RuntimeVariant",
)
async def v1_get_model_variant(
    model_id: str, variant_id: str, _key: ApiKey = Depends(require_api_key)
):
    descriptor = _get_public_model_or_404(model_id)
    for v in _runtime_variants_for_model(descriptor.id):
        if v.variantId == variant_id:
            return v
    raise HTTPException(
        status_code=404, detail=f"Variant '{variant_id}' not found for model '{model_id}'"
    )


def _model_can_use_voice(descriptor, has_reference_audio: bool) -> bool:
    caps = descriptor.capabilities
    if has_reference_audio:
        return bool(caps.supports_reference_audio)
    return bool(caps.supports_voice_optional)


@router.get(
    "/voices/{voice_id}/compatible-models",
    response_model=V1CompatibleModels,
    summary="List models compatible with a voice",
)
async def v1_voice_compatible_models(
    voice_id: str,
    _key: ApiKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Models that can realize/serve this voice — computed from declared capabilities."""
    voice = await get_voice_by_public_id(db, voice_id)
    if voice is None:
        raise HTTPException(status_code=404, detail="Voice not found")
    has_ref = bool(await resolve_voice_audio_key(voice.id))
    models = [
        _model_summary(m)
        for m in model_registry.list_models(edition=app_settings.EDITION)
        if _model_can_use_voice(m, has_ref)
    ]
    return V1CompatibleModels(voiceId=voice_id, models=models)


@router.get(
    "/voices/{voice_id}/compatible-variants",
    response_model=V1CompatibleVariants,
    summary="List RuntimeVariants compatible with a voice",
)
async def v1_voice_compatible_variants(
    voice_id: str,
    modelId: Optional[str] = Query(None),
    _key: ApiKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    """RuntimeVariants that can serve this voice, optionally filtered to one model."""
    voice = await get_voice_by_public_id(db, voice_id)
    if voice is None:
        raise HTTPException(status_code=404, detail="Voice not found")
    has_ref = bool(await resolve_voice_audio_key(voice.id))

    if modelId is not None:
        descriptors = [_get_public_model_or_404(modelId)]
    else:
        descriptors = [
            m for m in model_registry.list_models(edition=app_settings.EDITION)
            if _model_can_use_voice(m, has_ref)
        ]

    variants: list[V1RuntimeVariant] = []
    for descriptor in descriptors:
        if not _model_can_use_voice(descriptor, has_ref):
            continue
        for v in _runtime_variants_for_model(descriptor.id):
            # Filter by the variant's own declared capabilities when reference
            # audio is involved; otherwise include all of the model's variants.
            if has_ref and v.capabilities and "reference_audio" not in v.capabilities:
                continue
            variants.append(v)
    return V1CompatibleVariants(voiceId=voice_id, modelId=modelId, variants=variants)


@router.get("/voices", response_model=V1VoiceList, summary="List voices")
async def v1_list_voices(
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = None,
    _key: ApiKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    items, next_cursor = await list_voices_page(db, scope="mine", limit=limit, cursor=cursor)
    return V1VoiceList(
        voices=[
            V1Voice(voiceId=v.public_voice_id, name=v.name, language=v.language)
            for v in items
        ],
        nextCursor=next_cursor,
    )


@router.get("/voices/{voice_id}", response_model=V1VoiceDetail, summary="Get a voice")
async def v1_get_voice(
    voice_id: str,
    _key: ApiKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    voice = await get_voice_by_public_id(db, voice_id)
    if voice is None:
        raise HTTPException(status_code=404, detail="Voice not found")
    return _to_detail(voice)


@router.post("/voices", response_model=V1VoiceDetail, status_code=201, summary="Create a voice")
async def v1_create_voice(
    name: str = Form(...),
    transcript: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    language_code: Optional[str] = Form(None),
    file: UploadFile = File(...),
    _key: ApiKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    profile_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    try:
        # crop_end caps the reference at the public 10s limit (server-side enforcement).
        meta = await _process_and_upload(
            profile_id, file, 0.0, PUBLIC_REF_AUDIO_LIMIT_S,
            name=name, language=language, transcript=transcript,
            created_at=now.isoformat(),
        )
    except Exception as exc:
        await storage.delete_prefix(f"voices/{profile_id}/")
        raise HTTPException(status_code=422, detail=f"Audio processing failed: {exc}")

    voice = VoiceProfile(
        id=profile_id,
        name=name,
        language=language,
        language_code=language_code,
        transcript=transcript,
        audio_filename="reference.wav",
        audio_duration=meta["duration"],
        meta=meta,
        characteristics=characteristics_from_defaults(None, language=language),
    )
    db.add(voice)
    await db.commit()
    await db.refresh(voice)
    logger.info("Created voice %s via API (%s)", voice.public_voice_id, profile_id)
    return _to_detail(voice)


@router.delete("/voices/{voice_id}", summary="Delete a voice")
async def v1_delete_voice(
    voice_id: str,
    _key: ApiKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    voice = await get_voice_by_public_id(db, voice_id)
    if voice is None:
        raise HTTPException(status_code=404, detail="Voice not found")
    await storage.delete_prefix(f"voices/{voice.id}/")
    await db.delete(voice)
    await db.commit()
    return {"deleted": voice_id}


@router.post("/text-to-speech", summary="Generate speech (voice + text)")
async def v1_text_to_speech(
    payload: TextToSpeechRequest,
    request: Request,
    response: str = Query("stream", pattern="^(stream|url)$"),
    _key: ApiKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Synchronously generate speech and return it as a stream or a download URL.

    The pipeline is the same job-based generation used by the app, so a voice's saved
    generation defaults (and voice design) are applied automatically.
    """
    voice = await get_voice_by_public_id(db, payload.voiceId)
    if voice is None:
        raise HTTPException(status_code=404, detail="Voice not found")

    # Resolve the model (None = platform default).
    try:
        model = model_registry.get_or_default(payload.modelId)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Model '{payload.modelId}' not found")
    if model.activation_status != "active":
        raise HTTPException(status_code=409, detail=f"Model '{model.id}' is not available")

    # Validate an explicit RuntimeVariant selection (ADR-0020). Omitted → model default.
    if payload.variantId is not None:
        known = {v.variantId for v in _runtime_variants_for_model(model.id)}
        # When the runtime subsystem exposes no variants, only the synthesized
        # 'base' is addressable; reject anything else rather than silently ignore.
        allowed = known or {"base"}
        if payload.variantId not in allowed:
            raise HTTPException(
                status_code=404,
                detail=f"Variant '{payload.variantId}' not found for model '{model.id}'",
            )

    ref_key = await resolve_voice_audio_key(voice.id)
    # Only models that need reference audio require it.
    if not ref_key and model.capabilities.supports_reference_audio:
        raise HTTPException(status_code=404, detail="Voice audio not found")

    # Apply the voice's saved defaults so the API matches in-app behavior (Sub-project E).
    defaults = voice.generation_defaults or {}
    voice_design = defaults.get("voice_design") or []
    gen_params = {
        "num_step": defaults.get("num_step", 32),
        "guidance_scale": defaults.get("guidance_scale", 2.0),
        "speed": defaults.get("speed"),
        "duration": defaults.get("duration"),
        "t_shift": defaults.get("t_shift", 0.1),
        "denoise": defaults.get("denoise", True),
    }

    # Generation v2 overrides (ADR-0020), precedence: providerSettings >
    # generationSettings > voice defaults. Omitting both reproduces v1 behavior.
    if payload.generationSettings:
        schema = model.settings_schema
        if schema is not None:
            allowed_keys = set(schema.properties.keys())
            unknown = [k for k in payload.generationSettings if k not in allowed_keys]
            if unknown:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Unsupported generationSettings for model '{model.id}': "
                        f"{', '.join(sorted(unknown))}. Allowed: {', '.join(sorted(allowed_keys))}."
                    ),
                )
        gen_params.update(payload.generationSettings)
    if payload.providerSettings:
        # Untyped, model-specific pass-through; the adapter ignores keys it
        # does not understand. Never validated at the API boundary.
        gen_params.update(payload.providerSettings)
    if payload.variantId is not None:
        gen_params["runtime_variant_id"] = payload.variantId

    output_key = f"generated/{os.urandom(8).hex()}.wav"
    job = GenerationJob(
        text=payload.text,
        model_id=model.id,
        voice_profile_id=voice.id,
        ref_audio_path=ref_key,
        ref_text=voice.transcript,
        language=payload.language or voice.language_code,
        instruct=", ".join(voice_design) if voice_design else None,
        generation_params=gen_params,
        output_path=output_key,
    )
    db.add(job)
    voice.usage_count = (voice.usage_count or 0) + 1
    voice.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)

    # Run synchronously — the public API returns the finished audio in one call.
    await _process_job(job.id)
    await db.refresh(job)
    if job.status != "completed" or not job.output_path:
        raise HTTPException(status_code=500, detail=job.error_message or "Generation failed")

    fmt = payload.format
    filename = Path(job.output_path).name
    if response == "url":
        audio_url = (
            f"/audio/{filename}" if fmt == "wav" else f"/convert/{fmt}/{filename}"
        )
        return TextToSpeechUrlResponse(
            jobId=job.id, audioUrl=audio_url, format=fmt, durationSeconds=job.audio_duration
        )

    out_key = job.output_path if fmt == "wav" else await _ensure_format(job.output_path, fmt)
    content_type = "audio/wav" if fmt == "wav" else AUDIO_FORMATS[fmt]["content_type"]
    return await stream_object(
        out_key, request=request, content_type=content_type,
        download_name=f"omnivoice-{job.id}.{fmt}",
    )
