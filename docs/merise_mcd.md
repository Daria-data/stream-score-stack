# MCD — Modèle Conceptuel de Données

Diagramme entité-association (MERISE) pour le projet Olympic Results.

## Entités et associations

```mermaid
erDiagram
    COUNTRY {
        int id_country PK
        string country_name
    }

    FEDERATION {
        int id_federation PK
        string federation_name
        string federation_short
    }

    SPORT {
        int id_sport PK
        string sport_name_fr
        string sport_name_en
    }

    DISCIPLINE {
        int id_discipline PK
        string discipline_name
    }

    EPREUVE {
        int id_epreuve PK
        string epreuve_name
        string genre
        string epreuve_type
        bool is_individual
        bool is_olympic
        bool is_summer
        bool is_handicap
        int result_direction
    }

    EDITION {
        int id_edition PK
        int season_year
        date start_date
        date end_date
        string city
        string host_country
        string competition_type
    }

    EVENEMENT {
        int id_evenement PK
        string event_name_fr
        string event_name_en
        string age_category
    }

    RESULT {
        int id_result PK
        int id_athlete
        string athlete_last_name
        string athlete_first_name
        int id_team
        string team_name
        int rank
        string performance_text
        float performance_value
        string source_id
        datetime created_at
        datetime updated_at
    }

    FEDERATION ||--o{ SPORT : "governs"
    SPORT ||--o{ DISCIPLINE : "contains"
    DISCIPLINE ||--o{ EPREUVE : "defines"
    EPREUVE ||--o{ EVENEMENT : "instantiated_in"
    EDITION ||--o{ EVENEMENT : "hosts"
    EVENEMENT ||--o{ RESULT : "produces"
    COUNTRY ||--o{ RESULT : "represented_by"
```

## Cardinalités

| Association | Entité A | Card. | Entité B | Card. |
|---|---|---|---|---|
| governs | FEDERATION | 1,1 | SPORT | 0,N |
| contains | SPORT | 1,1 | DISCIPLINE | 0,N |
| defines | DISCIPLINE | 1,1 | EPREUVE | 0,N |
| instantiated_in | EPREUVE | 1,1 | EVENEMENT | 0,N |
| hosts | EDITION | 1,1 | EVENEMENT | 0,N |
| produces | EVENEMENT | 1,1 | RESULT | 0,N |
| represented_by | COUNTRY | 1,1 | RESULT | 0,N |
