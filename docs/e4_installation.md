# E4 — Installation et environnement

Guide pas-à-pas pour reproduire le projet sur une machine de développement (Windows / Linux / macOS).

---

## 1. Prérequis

| Outil | Rôle | Documentation |
|-------|------|-----------------|
| **Git** | Cloner le dépôt | — |
| **Docker Desktop** | Orchestration Postgres, loaders, Streamlit, API, Airflow | [Docker Compose](https://docs.docker.com/compose/) |
| **uv** | Environnement Python et dépendances | [uv](https://docs.astral.sh/uv/) — [repo](https://github.com/astral-sh/uv) |

Vérifications rapides :

```bash
git --version
docker compose version
uv --version
```

---

## 2. Cloner le dépôt

```bash
git clone <URL-du-depot>
cd stream-score-stack
```

---

## 3. Dépendances Python (hors Docker)

À la racine du projet (chaque dossier avec `pyproject.toml` utilise **uv** uniquement) :

```bash
uv sync --group core
```

- Groupe `core` : pandas, streamlit, sqlalchemy, fastapi, duckdb, httpx, etc.  
- Optionnel : `uv sync --group dev` (ruff, pytest), `uv sync --group airflow` si exécution locale d’Airflow.

Référence officielle : [Installing packages](https://docs.astral.sh/uv/concepts/projects/).

---

## 4. Préparation des sources de données (une fois)

Le script prépare les fichiers utilisés par les extracteurs (API mock, HTML, Parquet, CSV source DB, etc.) :

```bash
uv run python scripts/prepare_sources.py
```

---

## 5. Variables d’environnement (optionnel en local)

Créer un fichier `.env` à la racine **uniquement si** vous personnalisez la base (ne pas commiter de secrets). Exemple :

```text
DB_HOST=localhost
DB_PORT=5433
DB_NAME=sports
DB_USER=postgres
DB_PASSWORD=postgres
```

Avec Docker, les services reçoivent `DB_HOST=postgres` et `DB_PORT=5432` via `docker-compose.yml`.

---

## 6. Pipelines en local (sans Docker, pour développement)

Ordre recommandé :

```bash
uv run python -m src.pipelines.extract.run_extraction
uv run python -m src.pipelines.sql.run_sql_extraction
uv run python -m src.pipelines.transform.run_aggregation
```

Pour l’extraction API : démarrer le mock API (`docker compose up -d mock-api`) ou définir `MOCK_API_URL`.

Pour Postgres / DuckDB : la base doit être joignable (`DB_HOST`, `DB_PORT`).

Import cible :

```bash
uv run python src/db/import_final_dataset.py
```

---

## 7. Stack complète avec Docker

À la racine :

```bash
docker compose up -d --build
```

Séquence typique :

1. **postgres** — santé OK  
2. **loader** — exécute `import_final_dataset.py` (schéma cible + CSV `data/final/`)  
3. **app** — Streamlit :8501  
4. **api** — REST :8888  
5. **mock-api** — :8000  
6. **airflow-*** — UI :8080  

Vérification :

```bash
docker compose ps
```

Réinitialisation complète (données Postgres recréées) :

```bash
docker compose down -v
docker compose up -d --build
```

**Important** : avant un `down -v`, s’assurer que `data/final/*.csv` est à jour (pipelines locaux ou DAG `e4_pipeline`).

---

## 8. Ports exposés (référence)

| Port | Service |
|------|---------|
| 5433 | PostgreSQL (hôte → conteneur 5432) |
| 8000 | Mock API |
| 8080 | Airflow Web |
| 8501 | Streamlit |
| 8888 | API REST E4 |

---

## 9. Dépannage

| Symptôme | Piste |
|----------|--------|
| `loader` en erreur | Vérifier présence de `data/final/*.csv` et montages `./data/final`, `./sql` |
| API sans données | Attendre `loader` terminé ; vérifier `docker logs sports-loader` |
| Extraction API échoue | Mock API démarré ; `MOCK_API_URL` si hors réseau Docker |
| Airflow DAG en erreur | Voir logs scheduler ; dépendances `_PIP_ADDITIONAL_REQUIREMENTS` dans `docker-compose.yml` |

---

## 10. Suite

- Démo guidée : [e4_demo_steps.md](e4_demo_steps.md)  
- SQL documenté : [e4_sql_documentation.md](e4_sql_documentation.md)  
- API : [e4_api_usage.md](e4_api_usage.md)
