# peakvox/f5-tts-runtime Dockerfile.
#
# Mirrors runtime-registry/kokoro-82m/Dockerfile (R8 reference)
# with two adjustments:
#   1. Base image: CUDA-enabled PyTorch (F5-TTS is GPU-only).
#      The Kokoro reference uses python:3.11-slim because Kokoro
#      is CPU-capable; F5-TTS is not, so the base must provide
#      a CUDA runtime.
#   2. System deps: ffmpeg + libsndfile (audio I/O), and the
#      CUDA libraries that ship with the PyTorch base image.
#
# Image tag: peakvox/f5-tts-runtime:0.1.0 (matches the
# descriptor's spec.image.repository + tag; spec.image.digest
# is set by the build script after a successful `docker build`).

FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps:
#   - ffmpeg: audio decoding
#   - libsndfile1: required by soundfile/torchaudio
#   - build-essential: required for some pip wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer cache for the
# requirements that change less often than the source).
COPY requirements.txt /app/requirements.txt

# f5-tts 1.0.3 upgrades torch (e.g. 2.4.0 → 2.12+cu130) via transitive deps
# (bitsandbytes, accelerate). After f5-tts installs, torchaudio and torchvision
# are still compiled against the OLD torch ABI and fail to load. Re-install them
# from the matching cu-index so their ABI agrees with whatever torch ended up installed.
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    CUDA_TAG=$(python3 -c "import torch; v=torch.version.cuda; print('cu' + v.replace('.','') if v else 'cpu')") && \
    echo "torch $(python3 -c 'import torch; print(torch.__version__)') → reinstalling torchaudio+torchvision for ${CUDA_TAG}" && \
    pip install --no-cache-dir --upgrade torchaudio torchvision \
        --index-url "https://download.pytorch.org/whl/${CUDA_TAG}" && \
    pip install --no-cache-dir torchcodec && \
    python3 -c "import torch, torchaudio; print('ABI OK — torch', torch.__version__, 'torchaudio', torchaudio.__version__)"

# Copy the runtime service entrypoint.
COPY server.py /app/server.py

# The descriptor's spec.service.port is 8000. EXPOSE documents
# the port; the runtime driver maps it to a host port at run
# time. The Docker driver MUST be configured with --gpus=all for
# the container to claim a CUDA device.
EXPOSE 8000

# Healthcheck: probe /health every 10s; the service returns 200
# even when the model is still loading (liveness only).
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" \
    || exit 1

# The runtime service contract: uvicorn serves the FastAPI app
# on 0.0.0.0:8000. The descriptor's spec.service.port must
# match.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
