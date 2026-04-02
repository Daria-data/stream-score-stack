FROM python:3.12-slim

RUN pip install --no-cache-dir fastapi uvicorn

WORKDIR /app
COPY src/mock_api/ /app/src/mock_api/
COPY data/mock_api/ /app/data/mock_api/

EXPOSE 8000
CMD ["uvicorn", "src.mock_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
