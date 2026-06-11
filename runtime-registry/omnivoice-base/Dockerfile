# peakvox/omnivoice-runtime Dockerfile.
#
# Mirrors runtime-registry/kokoro-82m/Dockerfile (R8 reference).
# Adjustments from the Kokoro template:
#   1. Image tag: peakvox/omnivoice-runtime:0.1.5
#      (matches descriptor's spec.image.repository + tag).
#   2. Framework install: omnivoice==0.1.5
#      (replaces kokoro==0.7.16 + spacy).
#   3. No phonemizer system deps (OmniVoice uses Qwen3 tokenizer).
#   4. EXPOSE 8000 (descriptor's spec.service.port).
#   5. CMD: uvicorn server:app --host 0.0.0.0 --port 8000
#      (same as Kokoro — the Runtime Service Contract is stable).
#
# Base image: pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime.
#   This image ships torch 2.8.0+cu128, torchaudio 2.8.0+cu128, and
#   torchvision 0.23.0+cu128 already installed and ABI-matched against
#   one CUDA 12.8 stack. OmniVoice 0.1.5 only requires torch>=2.4 /
#   torchaudio>=2.4, so `pip install -r requirements.txt` keeps torch at
#   2.8.0 and never touches the CUDA stack.
#
#   We deliberately do NOT force-reinstall torch here. A previous
#   revision used a slim/CPU base and then ran
#   `pip install --force-reinstall torch==2.8.0+cu128 torchaudio==... \
#       torchvision --extra-index-url <cu128>`. That step failed the
#   build: torchvision was UNPINNED and `--extra-index-url` keeps PyPI
#   as the primary index, so pip resolved torchvision from PyPI against
#   a torch build that did not match the explicitly pinned
#   torch==2.8.0+cu128, producing a dependency-resolution / ABI break.
#   Pinning the whole stack at the base-image layer removes that entire
#   failure class — there is nothing left to re-resolve.
#
#   GPU vs CPU is selected at RUN time by the runtime driver
#   (DockerRuntimeDriver._device_requests reads the `use_gpu` setting):
#   with a GPU attached, torch.cuda.is_available() is True and the
#   model loads on CUDA; with no GPU attached, the same cu128 torch
#   build runs on CPU (torch.cuda.is_available() is False). The image
#   is identical for both modes.

FROM pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps:
#   - ffmpeg: required for audio decoding
#   - build-essential: required for some pip wheels (e.g. tokenizers)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer cache for the requirements
# that change less often than the source).
COPY requirements.txt /app/requirements.txt

# Install OmniVoice 0.1.5 on top of the pre-matched torch 2.8.0+cu128
# stack. omnivoice requires torch>=2.4 / torchaudio>=2.4, both already
# satisfied, so this does not move torch/torchaudio/torchvision. The
# final import asserts the ABI is intact before the layer is committed.
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    python3 -c "import torch, torchaudio, torchvision; assert torch.version.cuda, 'torch is not a CUDA build'; print('ABI OK — torch', torch.__version__, 'torchaudio', torchaudio.__version__, 'torchvision', torchvision.__version__)"

# Copy the runtime service entrypoint.
COPY server.py /app/server.py

# The descriptor's spec.service.port is 8000. EXPOSE documents the
# port; the runtime driver maps it to a host port at run time.
EXPOSE 8000

# Healthcheck: probe /health every 10s; the service returns 200
# even when the model is still loading (liveness only).
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" \
    || exit 1

# The runtime service contract: uvicorn serves the FastAPI app on
# 0.0.0.0:8000. The descriptor's spec.service.port must match.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
