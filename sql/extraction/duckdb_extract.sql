-- =============================================================================
-- DuckDB Extraction Queries (Big Data / Parquet Layer)
-- Target: data/parquet/athletes_teams.parquet
--
-- These queries demonstrate C9 requirements:
--   - SQL extraction from a big-data system (columnar storage)
--   - Aggregations, filtering, deduplication
--   - DuckDB as analytical SQL engine on Parquet
-- =============================================================================

-- Note: {PARQUET_PATH} is a placeholder replaced at runtime.
-- DuckDB read_parquet() provides zero-copy reads from columnar files.

-- -----------------------------------------------------------------------------
-- QUERY 1: Extract unique athletes
-- -----------------------------------------------------------------------------
-- Purpose: Deduplicate athlete records for dimension loading.
-- Why DISTINCT: Same athlete may appear in multiple result rows.
-- Filter: Exclude rows where athlete ID is NULL (team-only entries).

SELECT DISTINCT
    id_athlete_base_resultats AS id_athlete,
    athlete_nom AS last_name,
    athlete_prenom AS first_name,
    id_equipe AS id_team,
    equipe_en AS team_name
FROM read_parquet('{PARQUET_PATH}')
WHERE id_athlete_base_resultats IS NOT NULL
ORDER BY id_athlete;

-- -----------------------------------------------------------------------------
-- QUERY 2: Extract unique federations
-- -----------------------------------------------------------------------------
-- Purpose: Build federation dimension from parquet source.
-- Optimization: DuckDB pushes DISTINCT down to columnar scan.

SELECT DISTINCT
    id_federation,
    federation AS federation_name,
    federation_nom_court AS federation_short
FROM read_parquet('{PARQUET_PATH}')
ORDER BY id_federation;

-- -----------------------------------------------------------------------------
-- QUERY 3: Aggregation — athletes per federation
-- -----------------------------------------------------------------------------
-- Purpose: Analytical insight into federation representation.
-- Use case: Validate data distribution, identify dominant federations.

SELECT 
    id_federation,
    federation AS federation_name,
    COUNT(DISTINCT id_athlete_base_resultats) AS athlete_count
FROM read_parquet('{PARQUET_PATH}')
WHERE id_athlete_base_resultats IS NOT NULL
GROUP BY id_federation, federation
ORDER BY athlete_count DESC;

-- -----------------------------------------------------------------------------
-- QUERY 4: Aggregation — athletes per team
-- -----------------------------------------------------------------------------
-- Purpose: Understand team sizes in the dataset.
-- Filter: Only rows with both athlete and team info.

SELECT 
    id_equipe,
    equipe_en AS team_name,
    COUNT(DISTINCT id_athlete_base_resultats) AS member_count
FROM read_parquet('{PARQUET_PATH}')
WHERE id_athlete_base_resultats IS NOT NULL
  AND id_equipe IS NOT NULL
GROUP BY id_equipe, equipe_en
ORDER BY member_count DESC
LIMIT 20;

-- -----------------------------------------------------------------------------
-- QUERY 5: Extract teams without individual athletes
-- -----------------------------------------------------------------------------
-- Purpose: Identify pure team entries (no named athletes).
-- Use case: These represent collective results in team sports.

SELECT DISTINCT
    id_equipe,
    equipe_en AS team_name,
    id_federation,
    federation AS federation_name
FROM read_parquet('{PARQUET_PATH}')
WHERE id_athlete_base_resultats IS NULL
  AND id_equipe IS NOT NULL
ORDER BY id_equipe;

-- -----------------------------------------------------------------------------
-- QUERY 6: Data quality — records with missing federation
-- -----------------------------------------------------------------------------
-- Purpose: Find athletes/teams without federation assignment.
-- Use case: Data cleaning before final dataset.

SELECT 
    id_athlete_base_resultats,
    athlete_nom,
    id_equipe,
    equipe_en
FROM read_parquet('{PARQUET_PATH}')
WHERE id_federation IS NULL
LIMIT 100;
