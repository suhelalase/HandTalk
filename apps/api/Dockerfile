FROM python:3.11-slim

WORKDIR /app

ARG MODEL_URL=

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt

# Model (optional)
RUN if echo "$MODEL_URL" | grep -Eq '^https?://'; then \
      echo "Downloading model from MODEL_URL" && \
      curl -L --retry 3 --retry-delay 2 "$MODEL_URL" -o ./model.h5; \
    else \
      echo "MODEL_URL not set (or not a URL); building image without model" && \
      : > ./model.h5; \
    fi

# Copy app
COPY apps/api .

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run FastAPI with Uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}"]
