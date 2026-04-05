# Airflow : DAG `e4_pipeline`

Documentation technique du DAG d'orchestration bout-en-bout.

---

## 1. Vue d'ensemble

| Paramètre | Valeur |
|-----------|--------|
| `dag_id` | `e4_pipeline` |
| `schedule` | `@daily` (00:00 UTC) |
| `catchup` | `False`, pas de backfill automatique |
| `max_active_runs` | `1`, un seul run à la fois |
| `retries` (default) | `2` par task |
| `retry_delay` | `5 min` entre chaque tentative |

Déclenchement également possible en **manuel** depuis l'UI Airflow.

---

## 2. Graphe des tâches (5 tasks)

```
extract_multi_sources
        │
        ▼
   sql_extraction
        │
        ▼
aggregate_and_build_final
        │
        ▼
validate_final_dataset      ◄── gate : bloque l'import si CSV manquant, vide ou NULL sur PK/FK
        │
        ▼
 import_to_target_db
```

---

## 3. Détail des tâches

| Task | Module appelé | Rôle |
|------|---------------|------|
| `extract_multi_sources` | `src.pipelines.extract.run_extraction` | Extraction multi-sources vers `data/staging/*.csv` |
| `sql_extraction` | `src.pipelines.sql.run_sql_extraction` | Requêtes SQL documentées (PostgreSQL + DuckDB) vers staging |
| `aggregate_and_build_final` | `src.pipelines.transform.run_aggregation` | Normalize, Clean, Merge, Build : `data/final/*.csv` + `.parquet` |
| `validate_final_dataset` | *(inline dans le DAG)* | Vérifie les 8 CSV : existence, non-vide, NOT NULL sur PK et FK critiques |
| `import_to_target_db` | `src.db.import_final_dataset` | TRUNCATE + COPY dans PostgreSQL cible |

---

## 4. Validation pré-import

La tâche `validate_final_dataset` vérifie **avant** le chargement :

| Contrôle | Comportement en cas d'échec |
|----------|---------------------------|
| CSV absent (`FileNotFoundError`) | Task en erreur, import bloqué |
| CSV vide (0 lignes) | `ValueError`, import bloqué |
| NULL dans une colonne PK/FK requise | `ValueError` avec détail (table, colonne, count) |

Colonnes vérifiées par table :

| Table | Colonnes NOT NULL requises |
|-------|--------------------------|
| `dim_country` | `id_country` |
| `dim_federation` | `id_federation` |
| `dim_sport` | `id_sport`, `id_federation` |
| `dim_discipline` | `id_discipline` |
| `dim_epreuve` | `id_epreuve`, `id_discipline`, `id_sport` |
| `dim_edition` | `id_edition` |
| `dim_evenement` | `id_evenement`, `id_epreuve`, `id_edition` |
| `fact_result` | `id_result`, `id_evenement`, `id_country` |

---

## 5. Politique de reprise

- Chaque task est relancée automatiquement **2 fois** (`retries=2`) avec un délai de **5 minutes** (`retry_delay`).
- Si les 3 tentatives échouent, le task passe en `failed` et le DAG s'arrête (les tasks suivants ne s'exécutent pas).
- Le run peut être relancé manuellement depuis l'UI.

---

## 6. Variables d'environnement (conteneur Airflow)

Configurées dynamiquement par `_configure_runtime_env()` au début de chaque task :

| Variable | Valeur dans Docker |
|----------|-------------------|
| `DB_HOST` | `postgres` |
| `DB_PORT` | `5432` |
| `DB_NAME` | `sports` |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | `${DB_PASSWORD:-postgres}` |
| `MOCK_API_URL` | `http://mock-api:8000` |

---

## 7. Accès

| Élément | URL / commande |
|---------|---------------|
| UI Airflow | http://localhost:8080 (`admin` / `admin`) |
| Logs d'un task | UI : DAG, Grid, clic sur le task, **Log** |
| Trigger manuel | UI : DAG, bouton **▶ Trigger DAG** |
