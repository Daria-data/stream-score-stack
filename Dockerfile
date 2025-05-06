FROM python:3.12-slim

# --- install uv ---------------------------------------------------
RUN apt-get update && apt-get install -y curl build-essential \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -s /root/.local/bin/uv /usr/local/bin/uv

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
