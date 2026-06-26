FROM python:3.11-slim

WORKDIR /app

ARG USE_RENDER_REQUIREMENTS=false
ENV USE_RENDER_REQUIREMENTS=${USE_RENDER_REQUIREMENTS}

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev git cmake && \
    rm -rf /var/lib/apt/lists/*

COPY requirements*.txt ./
RUN if [ "$USE_RENDER_REQUIREMENTS" = "true" ]; then \
        pip install --no-cache-dir -r requirements-render.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

COPY . .

RUN mkdir -p /app/app/storage

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
