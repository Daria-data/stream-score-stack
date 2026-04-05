# E4 API Usage Guide (C12)

This document explains how to run and demonstrate the REST API layer built in Phase 6.

## 1) Service overview

- Base URL: `http://localhost:8888`
- OpenAPI docs: `http://localhost:8888/docs`
- ReDoc: `http://localhost:8888/redoc`
- Authentication: `X-API-Key` header for data endpoints
- Default demo key: `e4-demo-key-2026`

## 2) Start the stack

From the repository root:

```bash
docker compose up -d --build
docker compose ps
```

Expected:
- `sports-api` is `Up (healthy)`
- `sports-pg` is `Up (healthy)`
- `sports-loader` completed successfully (`Exited (0)`)

## 3) Authentication model

The API uses a simple API key strategy:

- Header name: `X-API-Key`
- Missing key -> `401 Unauthorized`
- Invalid key -> `403 Forbidden`

Health endpoint is public and does not require authentication.

> **Security note.** A built-in demo key (`e4-demo-key-2026`) is compiled into
> the image as a fallback so that `docker compose up` works without a `.env`
> file.  When the fallback is active, the API emits a **WARNING** at startup:
> `API_KEY env var not set, using built-in demo key.`
> In a production deployment, set `API_KEY` explicitly and remove the default.

## 4) Endpoints

### Public endpoint

- `GET /health`

### Protected endpoints (require `X-API-Key`)

- `GET /countries`
- `GET /countries/{country_id}`
- `GET /sports`
- `GET /federations`
- `GET /editions`
- `GET /results`
- `GET /results/{result_id}`
- `GET /stats/results-by-country`

## 5) Demo requests (copy/paste)

### Health check

```bash
curl -s http://localhost:8888/health
```

### Countries (first 5)

```bash
curl -s "http://localhost:8888/countries?limit=5" \
  -H "X-API-Key: e4-demo-key-2026"
```

### Sports (first 5)

```bash
curl -s "http://localhost:8888/sports?limit=5" \
  -H "X-API-Key: e4-demo-key-2026"
```

### Paginated results

```bash
curl -s "http://localhost:8888/results?page=1&page_size=10" \
  -H "X-API-Key: e4-demo-key-2026"
```

### Results filtered by country

```bash
curl -s "http://localhost:8888/results?page=1&page_size=10&country_id=46" \
  -H "X-API-Key: e4-demo-key-2026"
```

### Single result details

```bash
curl -s "http://localhost:8888/results/6045706" \
  -H "X-API-Key: e4-demo-key-2026"
```

### Top countries by number of results

```bash
curl -s "http://localhost:8888/stats/results-by-country?limit=10" \
  -H "X-API-Key: e4-demo-key-2026"
```

### Auth failure check (expected 401)

```bash
curl -i "http://localhost:8888/countries"
```

## 6) Swagger demo path (step-by-step)

1. Open `http://localhost:8888/docs`
2. Run `GET /health`
3. Expand a protected endpoint (for example `GET /countries`)
4. Click "Try it out"
5. Add header `X-API-Key` with value `e4-demo-key-2026`
6. Execute and inspect JSON response
7. Show pagination on `GET /results`
8. Show aggregation endpoint `GET /stats/results-by-country`

## 7) Troubleshooting

- If `sports-api` is not healthy:
  - `docker logs sports-api`
- If API returns DB connection errors:
  - ensure `sports-pg` is healthy
  - ensure `sports-loader` has finished successfully
- If tables are empty:
  - rerun the stack with full reset:

```bash
docker compose down -v
docker compose up -d --build
```

