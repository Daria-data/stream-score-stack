-- =============================================================================
-- PostgreSQL Extraction Queries
-- Target: source schema (épreuves, événements)
-- 
-- These queries demonstrate C9 requirements:
--   - SQL extraction from a database
--   - Filtering, joining, aggregation
--   - Documentation of query logic
-- =============================================================================

-- -----------------------------------------------------------------------------
-- QUERY 1: Extract all épreuves with discipline hierarchy
-- -----------------------------------------------------------------------------
-- Purpose: Get complete épreuve catalog with discipline and spécialité info.
-- Optimization: id_epreuve is indexed (PK), ORDER BY uses the index.
-- Why SELECT *: We need all columns for the target dim_epreuve table.

SELECT 
    id_epreuve,
    epreuve,
    epreuve_genre,
    epreuve_type,
    est_epreuve_individuelle,
    est_epreuve_olympique,
    est_epreuve_ete,
    est_epreuve_handi,
    epreuve_sens_resultat,
    id_discipline_administrative,
    discipline_administrative,
    id_specialite,
    specialite,
    id_sport
FROM source.epreuves
ORDER BY id_epreuve;

-- -----------------------------------------------------------------------------
-- QUERY 2: Extract événements with épreuve reference
-- -----------------------------------------------------------------------------
-- Purpose: Get all events (specific contests within editions).
-- Join rationale: We join to épreuves to ensure FK integrity before loading.
-- Filter: Only include événements whose épreuve exists in the catalog.

SELECT 
    ev.id_evenement,
    ev.evenement,
    ev.evenement_en,
    ev.categorie_age,
    ev.id_epreuve,
    ev.id_edition
FROM source.evenements ev
INNER JOIN source.epreuves ep ON ev.id_epreuve = ep.id_epreuve
ORDER BY ev.id_evenement;

-- -----------------------------------------------------------------------------
-- QUERY 3: Aggregation — count of épreuves per discipline
-- -----------------------------------------------------------------------------
-- Purpose: Analytical query to understand data distribution.
-- Use case: Validate that disciplines have reasonable épreuve counts.
-- GROUP BY: discipline_administrative provides human-readable grouping.

SELECT 
    id_discipline_administrative,
    discipline_administrative,
    COUNT(*) AS epreuve_count
FROM source.epreuves
GROUP BY id_discipline_administrative, discipline_administrative
ORDER BY epreuve_count DESC;

-- -----------------------------------------------------------------------------
-- QUERY 4: Filter — Olympic summer events only
-- -----------------------------------------------------------------------------
-- Purpose: Extract subset for summer Olympics analysis.
-- WHERE logic: est_epreuve_olympique = 1 AND est_epreuve_ete = 1
-- This filters out winter and non-Olympic épreuves.

SELECT 
    id_epreuve,
    epreuve,
    epreuve_genre,
    discipline_administrative
FROM source.epreuves
WHERE est_epreuve_olympique = 1
  AND est_epreuve_ete = 1
ORDER BY discipline_administrative, epreuve;

-- -----------------------------------------------------------------------------
-- QUERY 5: Aggregation — événements per edition
-- -----------------------------------------------------------------------------
-- Purpose: Count how many contests happened in each Olympic edition.
-- Use case: Data validation / trend analysis.
-- JOIN with dim_edition to show human-readable edition info instead of raw IDs.

SELECT 
    e.season_year,
    e.city,
    e.competition_type,
    COUNT(*) AS event_count
FROM source.evenements ev
JOIN dim_edition e ON ev.id_edition = e.id_edition
GROUP BY e.season_year, e.city, e.competition_type
ORDER BY e.season_year DESC;

-- -----------------------------------------------------------------------------
-- QUERY 6: Filter incomplete records (data quality)
-- -----------------------------------------------------------------------------
-- Purpose: Identify événements without proper épreuve reference.
-- Use case: Data cleaning — these rows should be excluded or fixed.
-- LEFT JOIN + WHERE NULL: standard pattern to find orphan records.

SELECT 
    ev.id_evenement,
    ev.evenement,
    ev.id_epreuve
FROM source.evenements ev
LEFT JOIN source.epreuves ep ON ev.id_epreuve = ep.id_epreuve
WHERE ep.id_epreuve IS NULL;
