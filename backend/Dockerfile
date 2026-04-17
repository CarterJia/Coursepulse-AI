FROM python:3.11-slim

WORKDIR /app

# Install CPU-only PyTorch first (~200MB vs ~2GB for CUDA version)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /app/backend
COPY scripts/cleanup_storage.sh /app/scripts/cleanup_storage.sh
RUN chmod +x /app/scripts/cleanup_storage.sh

WORKDIR /app/backend

ENV PYTHONPATH=/app/backend

CMD ["sh", "-c", "/app/scripts/cleanup_storage.sh && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
