# Livrable E4 : OlympScore

Ce document est le **point d’entrée principal** de la documentation E4 : il résume le périmètre (compétences C8–C12) et renvoie vers les guides détaillés.

---

## Carte des compétences

| Compétence | Thème | Où le montrer |
|------------|--------|----------------|
| **C8** | Extraction multi-sources | `src/pipelines/extract/`, `data/staging/`, [spécifications](docs/e4_specifications_extraction.md) |
| **C9** | Requêtes SQL documentées + exécution programmatique | `sql/extraction/`, `src/pipelines/sql/run_sql_extraction.py`, [SQL docs](docs/e4_sql_documentation.md) |
| **C10** | Agrégation, réconciliation multi-sources, dataset final | `src/pipelines/transform/`, `data/final/`, [procédure tri](docs/procedure_tri_donnees.md) §2.4 |
| **C11** | Modèle de données, BDD cible, RGPD | `sql/init_target_db.sql`, `docs/merise_*.md`, RGPD ci-dessous |
| **C12** | Partage des données (API REST + auth + accès DB) | `src/api/`, [API usage](docs/e4_api_usage.md), [DB access](docs/e4_db_access.md) |

**Orchestration** : DAG Airflow `e4_pipeline` (`dags/e4_pipeline.py`), 5 tâches : extract, requêtes SQL, agrégation, **validation**, import. Schedule `@daily`, retries automatiques. Voir [docs/e4_airflow.md](docs/e4_airflow.md).

---

## Documentation E4 (à lire dans cet ordre)

| Document | Contenu |
|----------|---------|
| [docs/e4_installation.md](docs/e4_installation.md) | Prérequis, `uv`, Docker, variables d’environnement, premier démarrage |
| [docs/e4_sql_documentation.md](docs/e4_sql_documentation.md) | Justification des requêtes SQL (PostgreSQL + DuckDB) |
| [docs/e4_api_usage.md](docs/e4_api_usage.md) | API REST, clé `X-API-Key`, exemples `curl` / Swagger |
| [docs/e4_specifications_extraction.md](docs/e4_specifications_extraction.md) | Spécifications d'extraction C8 : 5 sources, protocoles, staging |
| [docs/e4_db_access.md](docs/e4_db_access.md) | Matrice des accès DB, isolation réseau, gestion secrets |
| [docs/e4_airflow.md](docs/e4_airflow.md) | DAG Airflow : graphe, schedule, validation, retries |

---

## Modélisation & conformité (C11)

| Document | Rôle |
|----------|------|
| [docs/merise_mcd.md](docs/merise_mcd.md) | MCD |
| [docs/merise_mld.md](docs/merise_mld.md) | MLD |
| [docs/merise_mpd.md](docs/merise_mpd.md) | MPD |
| [docs/registre_traitements_rgpd.md](docs/registre_traitements_rgpd.md) | Registre des traitements (art. 30 RGPD) |
| [docs/procedure_tri_donnees.md](docs/procedure_tri_donnees.md) | Procédure de tri / qualité des données |

---

## Accès rapide aux services (après `docker compose up -d --build`)

| Service | URL / Port |
|---------|------------|
| Streamlit (SQL playground) | http://localhost:8501 |
| API REST (FastAPI + OpenAPI) | http://localhost:8888, docs : `/docs`, clé `X-API-Key` : `e4-demo-key-2026` |
| Mock API (source C8) | http://localhost:8000 |
| Airflow | http://localhost:8080 (`admin` / `admin`) |
| PostgreSQL | `localhost:5433` (base `sports`) |

---

## Référence technique (résumé)

- **Schéma cible** : 7 tables `dim_*` + `fact_result`, voir `sql/init_target_db.sql`.
- **Import cible** : **full refresh** (`TRUNCATE … CASCADE` puis reload depuis `data/final/`), reproductible et aligné sur le dernier run du pipeline ; pas de chargement incrémental dans ce périmètre E4 (voir [procedure_tri_donnees.md](docs/procedure_tri_donnees.md) §2.6).
- **Pipelines Python** : `uv run python -m src.pipelines.extract.run_extraction` puis `run_sql_extraction`, `run_aggregation` ; import : `src/db/import_final_dataset.py` (automatisé par le loader Docker et par le DAG).
- **Gestion des dépendances** : [uv](https://docs.astral.sh/uv/), `uv sync --group core`.
- **Tests** : `uv run pytest tests/ -v`, 39 tests (unit + intégration) couvrant normalisation, nettoyage, réconciliation multi-sources, auth API et endpoints REST.

Pour le détail d’installation ouvrir [docs/e4_installation.md](docs/e4_installation.md) 

---


