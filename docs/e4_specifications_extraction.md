# Spécifications d'extraction (C8)

Ce document décrit les **5 sources de données**, le protocole d'extraction,
le format de sortie et le pipeline programmatique.

---

## 1. Vue d'ensemble

```
CSV brut -> scripts/prepare_sources.py -> 5 sources simulées

    Source 1 : API REST (Mock)       -> data/mock_api/*.json
    Source 2 : HTML (scraping)       -> data/html/editions.html
    Source 3 : Parquet (Big Data)    -> data/parquet/athletes_teams.parquet
    Source 4 : PostgreSQL (legacy)   -> data/source_db/*.csv, schéma source
    Source 5 : Fichier CSV (fait)    -> data/raw/fact_resultats_epreuves.csv
```

---

## 2. Détail par source

| # | Source | Format | Protocole | Extracteur | Staging |
|---|--------|--------|-----------|------------|---------|
| 1 | Mock API | JSON | HTTP GET (`/countries`, `/sports`) | `extract_from_api.py` | `api_countries.csv`, `api_sports.csv` |
| 2 | HTML scraping | HTML table | Parsing BeautifulSoup (`<tr>/<td>`) | `extract_from_html.py` | `html_editions.csv` |
| 3 | Parquet (DuckDB) | Parquet columnar | SQL via DuckDB `read_parquet()` | `extract_from_parquet.py` | `parquet_athletes.csv`, `parquet_federations.csv` |
| 4 | PostgreSQL | Relationnel (source schema) | SQL via SQLAlchemy (`SELECT *`) | `extract_from_postgres.py` | `pg_epreuves.csv`, `pg_evenements.csv` |
| 5 | Fichier CSV | CSV UTF-8 | Lecture directe pandas | `extract_from_file.py` | `file_results.csv` |

---

## 3. Sortie commune

Tous les extracteurs produisent des fichiers **CSV UTF-8** dans `data/staging/`.
Chaque fichier est nommé `{source_type}.csv` et contient les colonnes brutes
du source, prêtes pour l'étape de normalisation (C10).

---

## 4. Exécution

### Tout-en-un (5 sources séquentielles)

```bash
uv run python -m src.pipelines.extract.run_extraction
```

### Source par source

```bash
uv run python -m src.pipelines.extract.extract_from_api
uv run python -m src.pipelines.extract.extract_from_html
uv run python -m src.pipelines.extract.extract_from_parquet
uv run python -m src.pipelines.extract.extract_from_postgres
uv run python -m src.pipelines.extract.extract_from_file
```

### Prérequis pour chaque source

| Source | Prérequis |
|--------|-----------|
| API    | `sports-mock-api` démarré (port 8000) ou `MOCK_API_URL` défini |
| HTML   | Fichier `data/html/editions.html` présent (`prepare_sources.py`) |
| Parquet | Fichier `data/parquet/athletes_teams.parquet` présent |
| PostgreSQL | `sports-pg` démarré (port 5433), source schema initialisé |
| CSV | `data/raw/fact_resultats_epreuves.csv` présent |

---

## 5. Variables d'environnement

| Variable | Défaut | Utilisée par |
|----------|--------|--------------|
| `MOCK_API_URL` | `http://localhost:8000` | Source 1 (API) |
| `DB_HOST` | `localhost` | Source 4 (PostgreSQL) |
| `DB_PORT` | `5433` | Source 4 |
| `DB_NAME` | `sports` | Source 4 |
| `DB_USER` | `postgres` | Source 4 |
| `DB_PASSWORD` | `postgres` | Source 4 |

---

## 6. Validation post-extraction

| Fichier staging | Lignes attendues | Contrôle |
|-----------------|-----------------|----------|
| `api_countries.csv` | ~212 | Pays uniques |
| `api_sports.csv` | ~66 | Sports uniques |
| `html_editions.csv` | ~170 | Éditions olympiques |
| `parquet_athletes.csv` | ~18 293 | Athlètes (avant dédoublonnage) |
| `parquet_federations.csv` | ~37 | Fédérations |
| `pg_epreuves.csv` | 529 | Épreuves + `id_sport` |
| `pg_evenements.csv` | 1 185 | Événements |
| `file_results.csv` | 35 690 | Résultats / faits |

---

## 7. Réconciliation multi-sources (C10, `merge_sources.py`)

Après extraction et nettoyage, le **merge layer** croise les sources
pour garantir la cohérence avant export vers le schéma cible.

| Dimension / Table | Sources croisées | Logique |
|-------------------|-----------------|---------|
| `dim_country` | API (référentiel) et CSV résultats | Vérifier que chaque `id_country` du CSV existe dans l'API |
| `dim_sport` | API (référentiel) et PG épreuves | Vérifier que chaque `id_sport` des épreuves existe dans l'API |
| `dim_federation` | API + Parquet | Fusion + dédoublonnage, priorité API |
| `dim_edition` | HTML (maître) et PG événements | Filtrer : ne garder que les éditions ayant ≥ 1 événement ; dédup par clé métier |
| `fact_result` | CSV résultats et toutes dims | FK-validation croisée (`id_country`, `id_evenement`) |

---

## 8. Orchestration Airflow

Le DAG `e4_pipeline` (`dags/e4_pipeline.py`) automatise :
`extract`, puis `sql_extraction`, puis `aggregate` (merge + réconciliation), puis `validate_final_dataset`, puis `import_to_target_db`.


