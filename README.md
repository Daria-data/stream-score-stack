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

- **pyproject.toml**: project metadata & uv configuration (groups: core, dev, airflow)
- **docker-compose.yml**: local orchestration for Postgres, loader, Airflow and app
- **dags/imitation_ingest_data.py**: Airflow DAG definitions
- **data/raw/**: original CSV of Olympic results
- **src/**:
    - **app.py** — Streamlit front-end
    - **config.py** — pydantic settings
    - **db/init_db.py** — data loader script 

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

The project infrastructure is defined and managed through **Docker Compose**. Each service has clear dependencies and conditions that control its execution:

### Services:

- **postgres**
  - PostgreSQL database with Olympic results data.
  - Always running service, exposes port **5433**.
  - Central data store (`sports` database, `jo` table).

- **loader**
  - Runs **only once** at startup to load CSV data into PostgreSQL.
  - **Depends on:** "postgres" (waits until database is healthy).
  - Stops automatically after completing the data ingestion.

- **app**
  - Streamlit application to query data interactively.
  - Exposes UI at port **8501**.
  - **Depends on:**
    - `postgres` (healthy database connection).
    - `loader` (successful completion).

- **airflow-init**
  - Initializes Airflow metadata table within project's existing PostgreSQL (`sports` database).
  - **Connects directly** to the existing Postgres database of the project.
  - Creates Airflow admin user (`admin`/`admin`).
  - Runs **only once** at initial setup.
  - **Depends on:** `postgres` (healthy database).

- **airflow-web**
  - Airflow Web UI to monitor and trigger DAGs.
  - Exposes interface at port **8080**.
  - **Depends on:**
    - `postgres` (healthy database connection).
    - `airflow-init` (successful completion).

- **airflow-scheduler**
  - Airflow scheduler to execute DAG tasks on defined schedules.
  - Continuous background service without port exposure.
  - **Depends on:**
    - `postgres` (healthy database connection).
    - `airflow-init` (successful completion).

### Startup Sequence & Conditions:

1. **postgres** starts first; provides database.
2. **loader** waits for postgres, loads data once and exits.
3. **app** waits for postgres and loader completion, available at port **8501**.
4. **airflow-init** waits for postgres, initializes Airflow tables and user, then exits.
5. **airflow-web** and **airflow-scheduler** wait for airflow-init, run continuously, UI at port **8080**.

This clear dependency structure ensures services launch smoothly and function predictably.

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

## Airflow
- Access the UI at http://localhost:8080 *(login: admin / admin)*
- DAG ingest_every_2_years runs every two calendar years on January 1 (for Winter & Summer Games)
- Monitor runs, trigger backfills and inspect logs

**Initial Scheduling Adjustment**:  
By default, the first scheduled run might start on an earlier date than expected.  
To manually align the DAG's next execution date (simulate that January 1, 2025, has already run), execute:
```powershell
docker compose exec airflow-web bash -c "
    airflow dags backfill ingest_every_2_years \
   -s 2025-01-01 -e 2025-01-01 --reset-dagruns
"
```
*After running this command, the next scheduled execution moves correctly to January 1, 2027.*

## Next Steps
1. **CI/CD** Pipeline: GitHub Actions to automate uv sync, linting (ruff), testing (pytest). Enforce ruff and mypy in CI for code quality and type safety
2. **Integration & Unit Tests**: Use pytest with a test database to validate loader logic, DAG tasks etc
3. Production Overrides: Create **docker-compose.prod.yml** with resource limits, TLS, separate networks and monitoring integrations
4. Data Quality Checks - maybe
5. **Better UI** : Add query history, templates, favorites and DataViz

