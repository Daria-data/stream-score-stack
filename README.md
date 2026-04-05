# OlympScore: Olympic Results Data Platform

End-to-end data platform for Olympic sports results: multi-source extraction, SQL processing, aggregation, normalized database, REST API and interactive SQL playground.

Project context: **BTS SIO SLAM : E4**; functional scope aligns with competencies **C8–C12**.

**E4 documentation hub:** start at **[README_E4.md](README_E4.md)** (links to installation, demo script, SQL docs, API docs, MERISE, and RGPD).

---

## Architecture

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Mock API    │   │  PostgreSQL  │   │   Parquet    │
│  (FastAPI)   │   │ source schema│   │  (DuckDB)    │
│  :8000       │   │  :5433       │   │  local file  │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                ┌─────────▼──────────┐
                │   EXTRACTION (C8)  │  + CSV file + HTML scraping
                │  src/pipelines/    │
                │  extract/          │
                └─────────┬──────────┘
                          │  data/staging/*.csv
                ┌─────────▼──────────┐
                │ SQL EXTRACTION (C9)│
                │  sql/extraction/   │
                └─────────┬──────────┘
                          │
                ┌─────────▼──────────┐
                │ AGGREGATION (C10)  │
                │  normalize, clean  │
                │  merge, build      │
                └─────────┬──────────┘
                          │  data/final/*.csv
                ┌─────────▼──────────┐
                │ TARGET DB (C11)    │
                │  7 dim + 1 fact    │
                │  PostgreSQL        │
                └────┬─────────┬─────┘
                     │         │
          ┌──────────▼──┐  ┌───▼──────────┐
          │ REST API    │  │  Streamlit   │
          │ (FastAPI)   │  │  SQL         │
          │ :8888       │  │  Playground  │
          │ (C12)       │  │  :8501       │
          └─────────────┘  └──────────────┘
                     │
          ┌──────────▼──────────┐
          │  Airflow (Phase 7)  │
          │  DAG e4_pipeline    │
          │  :8080              │
          └─────────────────────┘
```

## Prerequisites

- **Docker Desktop** (Docker Compose v2+)
- **uv** ([Astral UV](https://docs.astral.sh/uv/)) for local Python dependency management

## Quick Start

```bash
git clone https://github.com/Daria-data/stream-score-stack
cd stream-score-stack

# 1. Prepare data sources (one-time, from raw CSV)
uv sync --group core
uv run python scripts/prepare_sources.py

# 2. Run local pipelines (extraction, SQL, aggregation)
uv run python -m src.pipelines.extract.run_extraction
uv run python -m src.pipelines.sql.run_sql_extraction
uv run python -m src.pipelines.transform.run_aggregation

# 3. Start the full stack
docker compose up -d --build
```

## Services

| Service            | Container          | Port  | Description                              |
|--------------------|--------------------|-------|------------------------------------------|
| PostgreSQL         | sports-pg          | 5433  | Main database (source + target schemas)  |
| Mock API           | sports-mock-api    | 8000  | REST API data source (countries, sports) |
| Loader             | sports-loader      | -     | One-shot: loads data into target schema  |
| Streamlit App      | sportquery-app     | 8501  | Interactive SQL playground               |
| REST API           | sports-api         | 8888  | Authenticated API over normalized DB     |
| Airflow Web        | sports-airflow-web | 8080  | DAG monitoring UI (admin/admin)          |
| Airflow Scheduler  | sports-airflow-scheduler | - | Task executor                          |

## Data Sources (C8)

| Source       | Type              | Module                              |
|--------------|-------------------|-------------------------------------|
| Mock API     | REST API (JSON)   | `src/pipelines/extract/extract_from_api.py`     |
| CSV file     | Flat file         | `src/pipelines/extract/extract_from_file.py`    |
| HTML page    | Web scraping      | `src/pipelines/extract/extract_from_html.py`    |
| PostgreSQL   | Database (source) | `src/pipelines/extract/extract_from_postgres.py`|
| Parquet      | Big data (DuckDB) | `src/pipelines/extract/extract_from_parquet.py` |

## Database Schema (C11)

Normalized snowflake schema: 7 dimension tables + 1 fact table.

- `dim_country`, `dim_federation`, `dim_sport`, `dim_discipline`
- `dim_epreuve`, `dim_edition`, `dim_evenement`
- `fact_result` (~35,700 rows)

See: `sql/init_target_db.sql`, `docs/merise_mcd.md`, `docs/merise_mld.md`, `docs/merise_mpd.md`

## REST API (C12)

- Base URL: `http://localhost:8888`
- OpenAPI docs: `http://localhost:8888/docs`
- Auth: `X-API-Key: e4-demo-key-2026`

Endpoints: `/health`, `/countries`, `/sports`, `/federations`, `/editions`, `/results`, `/results/{id}`, `/stats/results-by-country`

See: `docs/e4_api_usage.md`

## Airflow Pipeline (Phase 7)

DAG `e4_pipeline` orchestrates the full E4 data pipeline:

1. `extract_multi_sources` (C8)
2. `sql_extraction` (C9)
3. `aggregate_and_build_final` (C10)
4. `import_to_target_db` (C11)

Access: `http://localhost:8080` (admin / admin)

Schedule: `@daily`, `catchup=False`, 2 retries per task. Includes a `validate_final_dataset` gate before DB import. See `docs/e4_airflow.md`.

## Tests

```bash
uv sync --group dev --group core
uv run pytest tests/ -v
```

39 tests: unit tests on the transform pipeline (normalize, clean, merge/reconciliation) + API auth + integration tests (FastAPI TestClient, mocked DB).

## Project Structure

```
stream-score-stack/
├── dags/                          # Airflow DAGs
│   ├── e4_pipeline.py             # E4 full pipeline DAG
│   └── imitation_ingest_data.py   # Original ingest DAG
├── data/
│   ├── raw/                       # Original CSV
│   ├── html/                      # Scraped HTML source
│   ├── mock_api/                  # JSON for mock API
│   ├── parquet/                   # Parquet big data source
│   ├── source_db/                 # CSVs for PG source schema
│   ├── staging/                   # Intermediate extraction results
│   └── final/                     # Final dim_*.csv + fact_result.csv
├── docker/
│   └── db-init/                   # SQL init scripts for Postgres
├── README_E4.md                   # E4 entry point + competency map
├── docs/
│   ├── e4_installation.md         # Setup (uv, Docker, troubleshooting)
│   ├── e4_demo_steps.md           # Oral demo walkthrough
│   ├── merise_mcd.md              # Conceptual data model
│   ├── merise_mld.md              # Logical data model
│   ├── merise_mpd.md              # Physical data model
│   ├── e4_sql_documentation.md    # SQL query documentation (C9)
│   ├── e4_api_usage.md            # API usage guide (C12)
│   ├── e4_specifications_extraction.md # Extraction specs (C8)
│   ├── e4_db_access.md            # DB access matrix (C12)
│   ├── e4_airflow.md              # Airflow DAG documentation
│   ├── registre_traitements_rgpd.md  # RGPD register
│   └── procedure_tri_donnees.md   # Data management procedure
├── sql/
│   ├── init_target_db.sql         # Target schema DDL
│   └── extraction/                # Documented SQL queries (C9)
├── src/
│   ├── app.py                     # Streamlit SQL playground
│   ├── config.py                  # Pydantic settings
│   ├── api/                       # REST API (C12)
│   ├── db/                        # Database loaders
│   ├── mock_api/                  # Mock API source service
│   └── pipelines/
│       ├── extract/               # C8 extraction modules
│       ├── sql/                   # C9 SQL extraction
│       └── transform/             # C10 aggregation pipeline
├── tests/                         # Unit + integration tests (pytest)
│   ├── test_normalize.py          # Column normalization
│   ├── test_clean_records.py      # Record cleaning
│   ├── test_merge_sources.py      # Cross-source reconciliation
│   ├── test_auth.py               # API key authentication
│   └── test_api_integration.py    # FastAPI endpoints
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Documentation

| Document                           | Competency | Path                                |
|------------------------------------|------------|-------------------------------------|
| **E4 index (start here)**          | C8–C12     | `README_E4.md`                      |
| Installation                       | -          | `docs/e4_installation.md`           |
| Demo walkthrough                   | -          | `docs/e4_demo_steps.md`             |
| MERISE MCD / MLD / MPD             | C11        | `docs/merise_*.md`                  |
| SQL extraction documentation       | C9         | `docs/e4_sql_documentation.md`      |
| API usage guide                    | C12        | `docs/e4_api_usage.md`             |
| Extraction specifications          | C8         | `docs/e4_specifications_extraction.md` |
| DB access configuration            | C12        | `docs/e4_db_access.md`             |
| RGPD : Registre des traitements    | C11        | `docs/registre_traitements_rgpd.md` |
| RGPD : Procédure tri données       | C11        | `docs/procedure_tri_donnees.md`     |
