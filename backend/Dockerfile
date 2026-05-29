# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps for OpenCV, moviepy, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libglib2.0-0 libsm6 libxext6 libxrender-dev \
    ffmpeg libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="ViTIP Team"
LABEL description="Vietnamese Traditional Instrument Preservation – FastAPI Backend"

# Runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 ffmpeg libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app/ app/

# Model files are mounted at runtime (see docker-compose.yml)
# Static output directory
RUN mkdir -p static/uploads static/predict

# Non-root user for security
RUN useradd -m -u 1001 vitip && chown -R vitip /app
USER vitip

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
