# Olympic Results SQL Playground

A local data playground for querying Olympic sports results using Streamlit, PostgreSQL and Apache Airflow.

## Prerequisites

- **Docker & Docker Compose** (v2+)
- **uv** (Astral UV) for dependency management

## Setup

1. **Clone the repository**  
   ```bash
   git clone https://github.com/Daria-data/stream-score-stack
   cd stream-score-stack

2. **Install dependencies**
```bash
uv sync --group core      # pandas, streamlit, sqlalchemy, psycopg2-binary, pydantic-settings, openpyxl
uv sync --group dev       # ruff, pytest
uv sync --group airflow   # apache-airflow ...
```
3. **Configure environment**
Create a file named .env in the project root containing:
```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sports
DB_USER=postgres
DB_PASSWORD=postgres
```
*change if you prefer another password*

## Project Structure

- **pyproject.toml**: project metadata & uv configuration (groups: core, dev, test)
- **docker-compose.yml**: local orchestration for Postgres, loader, Airflow and app
- **dags/**: Airflow DAG definitions
- **data/raw/**: original CSV of Olympic results
- **src/**:
    - **app.py** — Streamlit front-end
    - **config.py** — pydantic settings
    - **db/init_db.py** — loader script 

## Running the Full Stack
```bash
docker compose up -d
```
This will start:

1. **PostgreSQL** on port 5433 with database sports and table **jo**.
2. **Loader** to ingest and cast CSV data.
3. **Airflow init** to migrate metadata and create an admin user (admin/admin).
4. **Airflow web** UI (http://localhost:8080) and **scheduler**.
5. **Streamlit** app (http://localhost:8501).

## Streamlit Interface
### Sidebar
1. Table Info : 
    - Table name ...
    - Description ...
    - Last refresh: timestamp of the last successful DAG run
    - Column selector: choose which columns to display
    - Quick Templates: load predefined SQL with one click : 
        - *"Show head"*
        - *"Medal tally by country - 2024"*
        - *"Athlete medal tally"*

### Main Area
- **SQL editor**: displays the selected template or custom SQL *(fully editable)*
- **Run query** *execute and view results*
- **Download CSV / Excel** *export your results locally*

## Apache Airflow
- Access the UI at http://localhost:8080 *(login: admin / admin)*
- DAG ingest_every_2_years runs every two calendar years on January 1
- Monitor runs, trigger backfills, and inspect logs

## Next Steps
1. **CI/CD** Pipeline: GitHub Actions to automate uv sync, linting (ruff), testing (pytest). Enforce ruff and mypy in CI for code quality and type safety
2. **Integration & Unit Tests**: Use pytest with a test database to validate loader logic, DAG tasks etc
3. Production Overrides: Create **docker-compose.prod.yml** with resource limits, TLS, separate networks and monitoring integrations
4. Data Quality Checks - maybe
5. **Better UI** : Add query history, temploates, favorites and DataViz

