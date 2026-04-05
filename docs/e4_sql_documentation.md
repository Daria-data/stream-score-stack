# Documentation des requêtes SQL d'extraction (C9)

Ce document décrit les requêtes SQL utilisées pour l'extraction des données,
conformément à la compétence C9 du référentiel E4.

## Objectifs

- Extraire les données depuis une base de données PostgreSQL et un système analytique (DuckDB/Parquet)
- Documenter les choix de sélection, filtrage, jointures et agrégations
- Expliquer les optimisations appliquées

## Structure des fichiers

```
sql/extraction/
├── postgres_extract.sql   # Requêtes PostgreSQL (source schema)
└── duckdb_extract.sql     # Requêtes DuckDB (couche Parquet)
```

Exécution programmatique: `src/pipelines/sql/run_sql_extraction.py`

---

## Requêtes PostgreSQL

### Query 1: Extraction des épreuves

```sql
SELECT id_epreuve, epreuve, epreuve_genre, epreuve_type, ..., id_sport
FROM source.epreuves
ORDER BY id_epreuve;
```

| Élément | Justification |
|---------|---------------|
| SELECT colonnes | Toutes les colonnes dont `id_sport` pour la hiérarchie sport → discipline |
| ORDER BY id_epreuve | Utilise l'index PK pour un tri efficace |
| Pas de WHERE | On extrait le catalogue complet |

### Query 2: Extraction des événements avec jointure

```sql
SELECT ev.id_evenement, ev.evenement, ev.evenement_en, ...
FROM source.evenements ev
INNER JOIN source.epreuves ep ON ev.id_epreuve = ep.id_epreuve
ORDER BY ev.id_evenement;
```

| Élément | Justification |
|---------|---------------|
| INNER JOIN | Garantit l'intégrité référentielle: on n'extrait que les événements dont l'épreuve existe |
| ON ev.id_epreuve = ep.id_epreuve | Jointure sur la clé étrangère |
| ORDER BY | Préparation pour un chargement séquentiel ordonné |

### Query 3: Agrégation — épreuves par discipline

```sql
SELECT id_discipline_administrative, discipline_administrative,
       COUNT(*) AS epreuve_count
FROM source.epreuves
GROUP BY id_discipline_administrative, discipline_administrative
ORDER BY epreuve_count DESC;
```

| Élément | Justification |
|---------|---------------|
| COUNT(*) | Compte le nombre d'épreuves par discipline |
| GROUP BY | Agrégation sur l'identifiant et le nom (pour lisibilité) |
| ORDER BY DESC | Les disciplines les plus représentées en premier |

**Cas d'usage**: Validation de la distribution des données avant chargement.

### Query 4: Filtrage — épreuves olympiques d'été

```sql
SELECT id_epreuve, epreuve, epreuve_genre, discipline_administrative
FROM source.epreuves
WHERE est_epreuve_olympique = 1 AND est_epreuve_ete = 1
ORDER BY discipline_administrative, epreuve;
```

| Élément | Justification |
|---------|---------------|
| WHERE | Filtre combiné: olympique ET été (exclut hiver et non-olympiques) |
| Colonnes sélectionnées | Sous-ensemble pour analyse spécifique |

### Query 5: Agrégation — événements par édition

```sql
SELECT e.season_year, e.city, e.competition_type,
       COUNT(*) AS event_count
FROM source.evenements ev
JOIN dim_edition e ON ev.id_edition = e.id_edition
GROUP BY e.season_year, e.city, e.competition_type
ORDER BY e.season_year DESC;
```

**Cas d'usage**: Vérifier le nombre de compétitions par Olympiade (tendance historique). Le JOIN avec `dim_edition` permet d'afficher l'année, la ville et le type au lieu d'un ID technique.

### Query 6: Détection de données incomplètes

```sql
SELECT ev.id_evenement, ev.evenement, ev.id_epreuve
FROM source.evenements ev
LEFT JOIN source.epreuves ep ON ev.id_epreuve = ep.id_epreuve
WHERE ep.id_epreuve IS NULL;
```

| Élément | Justification |
|---------|---------------|
| LEFT JOIN + WHERE NULL | Pattern standard pour trouver les enregistrements orphelins |
| Cas d'usage | Nettoyage: identifier les événements sans épreuve valide |

---

## Requêtes DuckDB (Big Data / Parquet)

DuckDB est un moteur analytique en mémoire qui exécute du SQL directement sur des fichiers Parquet.
Cela démontre l'extraction depuis un "système big data" (C9).

### Query 1: Extraction des athlètes uniques

```sql
SELECT DISTINCT id_athlete_base_resultats AS id_athlete, ...
FROM read_parquet('data/parquet/athletes_teams.parquet')
WHERE id_athlete_base_resultats IS NOT NULL
ORDER BY id_athlete;
```

| Élément | Justification |
|---------|---------------|
| DISTINCT | Déduplication: un athlète peut apparaître dans plusieurs résultats |
| read_parquet() | Lecture directe du fichier columnar (zero-copy) |
| WHERE NOT NULL | Exclut les entrées équipe-seulement |

### Query 2: Extraction des fédérations

```sql
SELECT DISTINCT id_federation, federation, federation_nom_court
FROM read_parquet(...)
ORDER BY id_federation;
```

**Optimisation**: DuckDB pousse le DISTINCT vers le scan columnar.

### Query 3: Agrégation — athlètes par fédération

```sql
SELECT id_federation, federation, COUNT(DISTINCT id_athlete_base_resultats) AS athlete_count
FROM read_parquet(...)
WHERE id_athlete_base_resultats IS NOT NULL
GROUP BY id_federation, federation
ORDER BY athlete_count DESC;
```

**Cas d'usage**: Comprendre la représentation de chaque fédération.

### Query 4: Top 20 équipes par taille

```sql
SELECT id_equipe, equipe_en, COUNT(DISTINCT id_athlete_base_resultats) AS member_count
FROM read_parquet(...)
WHERE id_athlete_base_resultats IS NOT NULL AND id_equipe IS NOT NULL
GROUP BY id_equipe, equipe_en
ORDER BY member_count DESC
LIMIT 20;
```

| Élément | Justification |
|---------|---------------|
| LIMIT 20 | Requête exploratoire, on veut les plus grandes équipes |
| Double filtre | Exclut les entrées sans athlète ou sans équipe |

### Query 5: Équipes sans athlètes individuels

```sql
SELECT DISTINCT id_equipe, equipe_en, id_federation, federation
FROM read_parquet(...)
WHERE id_athlete_base_resultats IS NULL AND id_equipe IS NOT NULL
ORDER BY id_equipe;
```

**Cas d'usage**: Identifier les résultats collectifs (sports d'équipe).

### Query 6: Contrôle qualité — fédérations manquantes

```sql
SELECT id_athlete_base_resultats, athlete_nom, id_equipe, equipe_en
FROM read_parquet(...)
WHERE id_federation IS NULL
LIMIT 100;
```

**Cas d'usage**: Identifier les données sans fédération assignée.

---

## Exécution programmatique

Le script `src/pipelines/sql/run_sql_extraction.py`:

1. Parse les fichiers SQL et extrait les requêtes nommées
2. Exécute chaque requête via SQLAlchemy (Postgres) ou DuckDB natif
3. Sauvegarde les résultats dans `data/staging/sql_*.csv`
4. Génère un rapport de succès/erreur

```bash
uv run python -m src.pipelines.sql.run_sql_extraction
```

---

## Optimisations appliquées

| Technique | Où | Bénéfice |
|-----------|-----|----------|
| Index sur PK | Postgres source.epreuves, source.evenements | Tri et jointure efficaces |
| INNER JOIN | Query 2 | Élimine les orphelins à la source |
| LEFT JOIN + NULL | Query 6 | Détection des incohérences |
| DISTINCT pushdown | DuckDB | Déduplication au niveau du scan columnar |
| read_parquet() | DuckDB | Zero-copy lecture de fichiers Parquet |
| LIMIT | Requêtes exploratoires | Réduction du volume de sortie |

---

## Résultats attendus

| Requête | Source | Lignes approximatives |
|---------|--------|----------------------|
| PG Query 1 | Postgres | 529 épreuves |
| PG Query 2 | Postgres | 1 185 événements |
| PG Query 3 | Postgres | 75 disciplines |
| DuckDB Query 1 | Parquet | 18 293 athlètes |
| DuckDB Query 2 | Parquet | 37 fédérations |
