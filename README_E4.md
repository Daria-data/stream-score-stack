# Livrable E4 — Stream Score Stack

Ce document est le **point d’entrée** pour le jury : il résume le périmètre E4 (compétences C8–C12) et renvoie vers la documentation détaillée.

---

## Carte des compétences

| Compétence | Thème | Où le montrer |
|------------|--------|----------------|
| **C8** | Extraction multi-sources | `src/pipelines/extract/`, `data/staging/` |
| **C9** | Requêtes SQL documentées + exécution programmatique | `sql/extraction/`, `src/pipelines/sql/run_sql_extraction.py`, [docs/e4_sql_documentation.md](docs/e4_sql_documentation.md) |
| **C10** | Agrégation, nettoyage, dataset final | `src/pipelines/transform/`, `data/final/` |
| **C11** | Modèle de données, BDD cible, RGPD | `sql/init_target_db.sql`, `docs/merise_*.md`, RGPD ci-dessous |
| **C12** | Partage des données (API REST + auth + docs) | `src/api/`, [docs/e4_api_usage.md](docs/e4_api_usage.md) |

**Orchestration** : DAG Airflow `e4_pipeline` (`dags/e4_pipeline.py`) enchaîne extract → SQL → agrégation → import BDD.

---

## Documentation E4 (à lire dans cet ordre pour une démo)

| Document | Contenu |
|----------|---------|
| [docs/e4_installation.md](docs/e4_installation.md) | Prérequis, `uv`, Docker, variables d’environnement, premier démarrage |
| [docs/e4_demo_steps.md](docs/e4_demo_steps.md) | Scénario de démo pas-à-pas (jury) |
| [docs/e4_sql_documentation.md](docs/e4_sql_documentation.md) | Justification des requêtes SQL (PostgreSQL + DuckDB) |
| [docs/e4_api_usage.md](docs/e4_api_usage.md) | API REST, clé `X-API-Key`, exemples `curl` / Swagger |

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
| API REST (FastAPI + OpenAPI) | http://localhost:8888 — docs : `/docs` |
| Mock API (source C8) | http://localhost:8000 |
| Airflow | http://localhost:8080 (`admin` / `admin`) |
| PostgreSQL | `localhost:5433` (base `sports`) |

---

## Référence technique (résumé)

- **Schéma cible** : 7 tables `dim_*` + `fact_result` — voir `sql/init_target_db.sql`.
- **Pipelines Python** : `uv run python -m src.pipelines.extract.run_extraction` puis `run_sql_extraction`, `run_aggregation` ; import : `src/db/import_final_dataset.py` (automatisé par le loader Docker et par le DAG).
- **Gestion des dépendances** : [uv](https://docs.astral.sh/uv/) — `uv sync --group core`.

Pour le détail d’installation et de démonstration, ouvrir [docs/e4_installation.md](docs/e4_installation.md) et [docs/e4_demo_steps.md](docs/e4_demo_steps.md).

---


