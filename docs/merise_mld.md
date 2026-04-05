# MLD — Modèle Logique de Données

Transformation du MCD en schéma relationnel (3NF).

## Schéma relationnel

```
dim_country (id_country PK, country_name)

dim_federation (id_federation PK, federation_name, federation_short)

dim_sport (id_sport PK, sport_name_fr, sport_name_en, #id_federation FK→dim_federation)

dim_discipline (id_discipline PK, discipline_name)

dim_epreuve (id_epreuve PK, epreuve_name, genre, epreuve_type,
             is_individual, is_olympic, is_summer, is_handicap,
             result_direction, #id_discipline FK→dim_discipline,
             #id_sport FK→dim_sport)

dim_edition (id_edition PK, season_year, start_date, end_date,
             city, host_country, competition_type)

dim_evenement (id_evenement PK, event_name_fr, event_name_en,
               age_category, #id_epreuve FK→dim_epreuve, #id_edition FK→dim_edition)

fact_result (id_result PK, #id_evenement FK→dim_evenement, #id_country FK→dim_country,
             id_athlete, athlete_last_name, athlete_first_name,
             id_team, team_name, rank, performance_text, performance_value,
             source_id, created_at, updated_at)
```

## Diagramme MLD

```mermaid
erDiagram
    dim_country {
        INT id_country PK
        VARCHAR country_name
    }

    dim_federation {
        INT id_federation PK
        VARCHAR federation_name
        VARCHAR federation_short
    }

    dim_sport {
        INT id_sport PK
        VARCHAR sport_name_fr
        VARCHAR sport_name_en
        INT id_federation FK
    }

    dim_discipline {
        INT id_discipline PK
        VARCHAR discipline_name
    }

    dim_epreuve {
        INT id_epreuve PK
        VARCHAR epreuve_name
        VARCHAR genre
        VARCHAR epreuve_type
        BOOLEAN is_individual
        BOOLEAN is_olympic
        BOOLEAN is_summer
        BOOLEAN is_handicap
        INT result_direction
        INT id_discipline FK
        INT id_sport FK
    }

    dim_edition {
        INT id_edition PK
        INT season_year
        DATE start_date
        DATE end_date
        VARCHAR city
        VARCHAR host_country
        VARCHAR competition_type
    }

    dim_evenement {
        INT id_evenement PK
        VARCHAR event_name_fr
        VARCHAR event_name_en
        VARCHAR age_category
        INT id_epreuve FK
        INT id_edition FK
    }

    fact_result {
        INT id_result PK
        INT id_evenement FK
        INT id_country FK
        INT id_athlete
        VARCHAR athlete_last_name
        VARCHAR athlete_first_name
        INT id_team
        VARCHAR team_name
        INT rank
        VARCHAR performance_text
        DOUBLE performance_value
        VARCHAR source_id
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    dim_federation ||--o{ dim_sport : ""
    dim_discipline ||--o{ dim_epreuve : ""
    dim_sport ||--o{ dim_epreuve : ""
    dim_epreuve ||--o{ dim_evenement : ""
    dim_edition ||--o{ dim_evenement : ""
    dim_evenement ||--o{ fact_result : ""
    dim_country ||--o{ fact_result : ""
```

## Règles de passage MCD → MLD

1. Chaque entité → une table relationnelle.
2. L'identifiant de chaque entité → clé primaire (PK).
3. Associations (1,N) : la clé primaire du côté "1" migre comme FK dans la table du côté "N".
4. Pas d'association N:N dans ce modèle → pas de table associative nécessaire.
5. Attributs optionnels (athlete, team) : NULLable dans `fact_result` car certains résultats sont collectifs sans athlète nommé.
