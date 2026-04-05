-- =============================================================
-- Target database schema: Olympic Results (normalized)
-- Snowflake schema: 1 fact table + 7 dimension tables
-- =============================================================

BEGIN;

-- ---- Dimension: country ----
CREATE TABLE IF NOT EXISTS dim_country (
    id_country      INTEGER PRIMARY KEY,
    country_name    VARCHAR(120) NOT NULL
);

-- ---- Dimension: federation ----
CREATE TABLE IF NOT EXISTS dim_federation (
    id_federation       INTEGER PRIMARY KEY,
    federation_name     VARCHAR(200) NOT NULL,
    federation_short    VARCHAR(60)
);

-- ---- Dimension: sport ----
CREATE TABLE IF NOT EXISTS dim_sport (
    id_sport        INTEGER PRIMARY KEY,
    sport_name_fr   VARCHAR(120) NOT NULL,
    sport_name_en   VARCHAR(120) NOT NULL,
    id_federation   INTEGER REFERENCES dim_federation(id_federation)
);

CREATE INDEX IF NOT EXISTS idx_sport_federation ON dim_sport(id_federation);

-- ---- Dimension: discipline ----
CREATE TABLE IF NOT EXISTS dim_discipline (
    id_discipline       INTEGER PRIMARY KEY,
    discipline_name     VARCHAR(120) NOT NULL
);

-- ---- Dimension: epreuve (event type / test) ----
-- id_sport lives here because one discipline can span multiple sports
-- (e.g. Lutte: libre / gréco-romaine, Kayak: sprint / slalom).
CREATE TABLE IF NOT EXISTS dim_epreuve (
    id_epreuve          INTEGER PRIMARY KEY,
    epreuve_name        VARCHAR(200) NOT NULL,
    genre               VARCHAR(20)  NOT NULL,   -- Hommes / Femmes / Mixte / Open
    epreuve_type        VARCHAR(30)  NOT NULL,   -- Individuel / Equipe / Double
    is_individual       BOOLEAN NOT NULL DEFAULT TRUE,
    is_olympic          BOOLEAN NOT NULL DEFAULT TRUE,
    is_summer           BOOLEAN NOT NULL DEFAULT TRUE,
    is_handicap         BOOLEAN NOT NULL DEFAULT FALSE,
    result_direction    INTEGER,                  -- 0/1 flag from source
    id_discipline       INTEGER NOT NULL REFERENCES dim_discipline(id_discipline),
    id_sport            INTEGER NOT NULL REFERENCES dim_sport(id_sport)
);

CREATE INDEX IF NOT EXISTS idx_epreuve_discipline ON dim_epreuve(id_discipline);
CREATE INDEX IF NOT EXISTS idx_epreuve_sport ON dim_epreuve(id_sport);

-- ---- Dimension: edition (Olympic Games instance) ----
CREATE TABLE IF NOT EXISTS dim_edition (
    id_edition          INTEGER PRIMARY KEY,
    season_year         INTEGER     NOT NULL,
    start_date          DATE        NOT NULL,
    end_date            DATE        NOT NULL,
    city                VARCHAR(80) NOT NULL,
    host_country        VARCHAR(80) NOT NULL,
    competition_type    VARCHAR(30) NOT NULL      -- JO Été / JO Hiver
);

-- ---- Dimension: evenement (specific contest within an edition) ----
CREATE TABLE IF NOT EXISTS dim_evenement (
    id_evenement        INTEGER PRIMARY KEY,
    event_name_fr       VARCHAR(200) NOT NULL,
    event_name_en       VARCHAR(200) NOT NULL,
    age_category        VARCHAR(30),
    id_epreuve          INTEGER NOT NULL REFERENCES dim_epreuve(id_epreuve),
    id_edition          INTEGER NOT NULL REFERENCES dim_edition(id_edition)
);

CREATE INDEX IF NOT EXISTS idx_evenement_epreuve ON dim_evenement(id_epreuve);
CREATE INDEX IF NOT EXISTS idx_evenement_edition ON dim_evenement(id_edition);

-- ---- Fact: result ----
CREATE TABLE IF NOT EXISTS fact_result (
    id_result               INTEGER PRIMARY KEY,
    id_evenement            INTEGER     NOT NULL REFERENCES dim_evenement(id_evenement),
    id_country              INTEGER     NOT NULL REFERENCES dim_country(id_country),
    id_athlete              INTEGER,              -- NULL for pure team events
    athlete_last_name       VARCHAR(120),
    athlete_first_name      VARCHAR(120),
    id_team                 INTEGER,
    team_name               VARCHAR(200),
    rank                    INTEGER,
    performance_text        VARCHAR(120),
    performance_value       DOUBLE PRECISION,
    source_id               VARCHAR(30),
    created_at              TIMESTAMP,
    updated_at              TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_result_evenement  ON fact_result(id_evenement);
CREATE INDEX IF NOT EXISTS idx_result_country    ON fact_result(id_country);
CREATE INDEX IF NOT EXISTS idx_result_athlete    ON fact_result(id_athlete);

COMMIT;
