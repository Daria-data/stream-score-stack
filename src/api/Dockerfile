FROM python:3.12-slim

RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy psycopg2-binary pydantic-settings

WORKDIR /app
COPY src/api/ /app/src/api/

ENV PYTHONUNBUFFERED=1 \
    DB_HOST=postgres \
    DB_PORT=5432 \
    DB_NAME=sports \
    DB_USER=postgres

EXPOSE 8888
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8888"]
