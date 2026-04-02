FROM python:3.12-slim

# --- install uv via pip (avoids GitHub DNS issues in Docker build) ---
RUN apt-get update && apt-get install -y build-essential \
    && pip install --no-cache-dir uv \
    && uv --version

WORKDIR /app
COPY pyproject.toml uv.lock uv.toml ./
RUN uv sync --group core --no-dev

COPY src ./src
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    DB_HOST=postgres \
    DB_PORT=5432 \
    DB_NAME=sports \
    DB_USER=postgres

EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "src/app.py", "--server.port=8501", "--server.headless=true"]
