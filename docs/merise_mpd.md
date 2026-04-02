# MPD — Modèle Physique de Données

Implémentation du MLD sur PostgreSQL 15.

## Choix du SGBD

**PostgreSQL 15** : base relationnelle open-source, robuste, conforme SQL:2016,
support natif des types DATE, BOOLEAN, DOUBLE PRECISION et indexation B-tree.
Déjà utilisée dans le projet pour le stockage et Airflow.

## Spécifications physiques

| Table | Lignes estimées | Taille estimée |
|---|---|---|
| dim_country | 212 | < 1 KB |
| dim_federation | 37 | < 1 KB |
| dim_sport | 66 | < 1 KB |
| dim_discipline | 75 | < 1 KB |
| dim_epreuve | 529 | ~30 KB |
| dim_edition | 170 | ~10 KB |
| dim_evenement | 1 185 | ~100 KB |
| fact_result | 35 690 | ~5 MB |

## Index

- Toutes les clés primaires (PK) disposent d'un index unique automatique.
- Index supplémentaires B-tree sur les clés étrangères de `fact_result`
  (`id_evenement`, `id_country`, `id_athlete`) pour accélérer les JOIN.
- Index sur les FK dans `dim_sport`, `dim_discipline`, `dim_epreuve`, `dim_evenement`.

## Script DDL

Voir [`sql/init_target_db.sql`](../sql/init_target_db.sql).

## Diagramme physique

```mermaid
erDiagram
    dim_country {
        INTEGER id_country PK "NOT NULL"
        VARCHAR_120 country_name "NOT NULL"
    }

    dim_federation {
        INTEGER id_federation PK "NOT NULL"
        VARCHAR_200 federation_name "NOT NULL"
        VARCHAR_60 federation_short "NULLABLE"
    }

    dim_sport {
        INTEGER id_sport PK "NOT NULL"
        VARCHAR_120 sport_name_fr "NOT NULL"
        VARCHAR_120 sport_name_en "NOT NULL"
        INTEGER id_federation FK "→ dim_federation"
    }

    dim_discipline {
        INTEGER id_discipline PK "NOT NULL"
        VARCHAR_120 discipline_name "NOT NULL"
        INTEGER id_sport FK "NOT NULL → dim_sport"
    }

    dim_epreuve {
        INTEGER id_epreuve PK "NOT NULL"
        VARCHAR_200 epreuve_name "NOT NULL"
        VARCHAR_20 genre "NOT NULL"
        VARCHAR_30 epreuve_type "NOT NULL"
        BOOLEAN is_individual "NOT NULL DEFAULT TRUE"
        BOOLEAN is_olympic "NOT NULL DEFAULT TRUE"
        BOOLEAN is_summer "NOT NULL DEFAULT TRUE"
        BOOLEAN is_handicap "NOT NULL DEFAULT FALSE"
        INTEGER result_direction "NULLABLE"
        INTEGER id_discipline FK "NOT NULL → dim_discipline"
    }

    dim_edition {
        INTEGER id_edition PK "NOT NULL"
        INTEGER season_year "NOT NULL"
        DATE start_date "NOT NULL"
        DATE end_date "NOT NULL"
        VARCHAR_80 city "NOT NULL"
        VARCHAR_80 host_country "NOT NULL"
        VARCHAR_30 competition_type "NOT NULL"
    }

    dim_evenement {
        INTEGER id_evenement PK "NOT NULL"
        VARCHAR_200 event_name_fr "NOT NULL"
        VARCHAR_200 event_name_en "NOT NULL"
        VARCHAR_30 age_category "NULLABLE"
        INTEGER id_epreuve FK "NOT NULL → dim_epreuve"
        INTEGER id_edition FK "NOT NULL → dim_edition"
    }

    fact_result {
        INTEGER id_result PK "NOT NULL"
        INTEGER id_evenement FK "NOT NULL → dim_evenement"
        INTEGER id_country FK "NOT NULL → dim_country"
        INTEGER id_athlete "NULLABLE"
        VARCHAR_120 athlete_last_name "NULLABLE"
        VARCHAR_120 athlete_first_name "NULLABLE"
        INTEGER id_team "NULLABLE"
        VARCHAR_200 team_name "NULLABLE"
        INTEGER rank "NULLABLE"
        VARCHAR_120 performance_text "NULLABLE"
        DOUBLE_PRECISION performance_value "NULLABLE"
        VARCHAR_30 source_id "NULLABLE"
        TIMESTAMP created_at "NULLABLE"
        TIMESTAMP updated_at "NULLABLE"
    }

    dim_federation ||--o{ dim_sport : "id_federation"
    dim_sport ||--o{ dim_discipline : "id_sport"
    dim_discipline ||--o{ dim_epreuve : "id_discipline"
    dim_epreuve ||--o{ dim_evenement : "id_epreuve"
    dim_edition ||--o{ dim_evenement : "id_edition"
    dim_evenement ||--o{ fact_result : "id_evenement"
    dim_country ||--o{ fact_result : "id_country"
```
