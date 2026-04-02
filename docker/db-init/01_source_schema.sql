-- Source schema: simulates a legacy database with épreuves and événements.
-- Loaded at Postgres startup via docker-entrypoint-initdb.d.

CREATE SCHEMA IF NOT EXISTS source;

-- ── épreuves (event types / tests) ──────────────────────────────────

CREATE TABLE source.epreuves (
    id_epreuve                  INTEGER PRIMARY KEY,
    epreuve                     VARCHAR(200) NOT NULL,
    epreuve_genre               VARCHAR(20),
    epreuve_type                VARCHAR(30),
    est_epreuve_individuelle    INTEGER,
    est_epreuve_olympique       INTEGER,
    est_epreuve_ete             INTEGER,
    est_epreuve_handi           INTEGER,
    epreuve_sens_resultat       INTEGER,
    id_discipline_administrative INTEGER,
    discipline_administrative   VARCHAR(120),
    id_specialite               INTEGER,
    specialite                  VARCHAR(120)
);

-- ── événements (specific contests) ──────────────────────────────────

CREATE TABLE source.evenements (
    id_evenement    INTEGER PRIMARY KEY,
    evenement       VARCHAR(200) NOT NULL,
    evenement_en    VARCHAR(200),
    categorie_age   VARCHAR(30),
    id_epreuve      INTEGER REFERENCES source.epreuves(id_epreuve),
    id_edition      INTEGER
);

-- ── Load data from mounted CSV files ────────────────────────────────

COPY source.epreuves FROM '/source_db/epreuves.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY source.evenements FROM '/source_db/evenements.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
