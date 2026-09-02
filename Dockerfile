FROM python:3.11-slim

# libgl/libglib needed for trimesh's optional rendering backends; xvfb provides
# a virtual framebuffer so headless thumbnail rendering works without a GPU.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV LIBRARY_PATH=/data \
    CONFIG_PATH=/config \
    PYTHONUNBUFFERED=1

VOLUME ["/data", "/config"]
EXPOSE 8420

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8420/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8420"]
