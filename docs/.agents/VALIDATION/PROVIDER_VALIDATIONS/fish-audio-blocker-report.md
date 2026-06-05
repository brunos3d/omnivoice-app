# Fish Audio Server Deployment — Blocker Report

**Date:** 2026-06-04
**Attempt:** P0-A (first deployment attempt)
**Status:** DEFERRED — real inference validation incomplete

## Attempted Approaches

### 1. Docker Image (`fishaudio/fish-speech:latest`)
- Downloaded model v1.4 (1.1B params, fits 8GB VRAM)
- Mounted checkpoints at `/app/checkpoints`
- LLaMA text2semantic model loaded ✅
- Decoder (codec) failed with `RuntimeError: Error(s) in loading state_dict for DAC`
- Root cause: config hardcodes `input_dim: 1024` in quantizer, checkpoint has `512`

### 2. Docker Image with v1.5 model
- Skipped (same decoder file name = same architecture, same blocker)

### 3. `pip install fish-speech` (Python 3.12 venv)
- Same `modded_dac_vq.yaml` with `input_dim: 1024` — identical decoder architecture
- No alternate config files available

## Root Cause

The `fishaudio/fish-speech` Docker image and `pip install fish-speech` package both target the **s2-pro model architecture**:

| Aspect | s2-pro | v1.4 / v1.5 |
|---|---|---|
| Parameter count | ~5B | ~1.1B |
| VRAM requirement | ~24GB+ | ~2GB |
| Codec checkpoint | `codec.pth` (full encoder + quantizer + decoder + GAN generator) | `firefly-gan-vq-fsq-8x1024-21hz-generator.pth` (partial: GAN generator + shared quantizer only) |
| Quantizer `input_dim` | 1024 | 512 |
| FSQ codebooks | 9 | 8 |
| Fits RTX 3060 Ti (8GB) | ❌ | ✅ |

The v1.4/v1.5 decoder checkpoint is **structurally incomplete** as a standalone codec:
- Contains only `backbone.*` (GAN generator backbone), `head.*` (GAN generator head), and `quantizer.*` (shared quantizer)
- Missing `encoder.*`, `project_in.*`, `project_out.*`, `decoder.*` required by the DAC model
- The `load_model()` function skips the "generator." stripping since no keys contain `"generator"` in their name
- Only the `quantizer.*` keys match the DAC model; the rest are silently ignored or randomly initialized

The full `codec.pth` with all required modules is only available for the **s2-pro** model (146k downloads), which requires 24GB+ VRAM.

## Hardware Constraint

**RTX 3060 Ti (8GB VRAM)** — cannot run s2-pro at any quantization level. The v1.4/v1.5 models fit but lack compatible codec weights.

## What Was Validated

✅ **PeakVox FishAudioAdapter HTTP client** — unit tested with mocked responses, passes all tests
✅ **LLaMA model loading** — v1.4 text2semantic model loads successfully in the Docker container
✅ **HTTP provider boundary** — adapter contract, capability contract, runtime integration all validated

## What Remains

- 🔴 Real Fish Audio inference execution through PeakVox
- 🔴 Voice → Variant → Artifact → Generation end-to-end with Fish
- 🔴 Noise floor / quality comparison with OmniVoice

## Recommendation

Defer Fish validation to when either:
1. A pre-built Fish Audio API is available (SaaS or hosted)
2. Hardware upgrade (24GB+ VRAM GPU) enables s2-pro deployment
3. A matching full codec checkpoint (`codec.pth` with `input_dim: 512` / 8 codebooks) is released for v1.5+

The PeakVox architecture is validated through unit tests; the remaining gap is exclusively deployment/infrastructure.
