# MLD : Modèle Logique de Données

Transformation du MCD en schéma relationnel (3NF).

## Schéma relationnel

<pre style="background:#ffffff;color:#000000;border:1px solid #000000;padding:12px;line-height:1.4;font-family:ui-monospace,Cascadia Code,Consolas,monospace;font-size:0.9em;margin:0;white-space:pre-wrap;">
dim_country (id_country PK, country_name)

dim_federation (id_federation PK, federation_name, federation_short)

dim_sport (id_sport PK, sport_name_fr, sport_name_en, #id_federation FK vers dim_federation)

dim_discipline (id_discipline PK, discipline_name)

dim_epreuve (id_epreuve PK, epreuve_name, genre, epreuve_type,
             is_individual, is_olympic, is_summer, is_handicap,
             result_direction, #id_discipline FK vers dim_discipline,
             #id_sport FK vers dim_sport)

dim_edition (id_edition PK, season_year, start_date, end_date,
             city, host_country, competition_type)

dim_evenement (id_evenement PK, event_name_fr, event_name_en,
               age_category, #id_epreuve FK vers dim_epreuve, #id_edition FK vers dim_edition)

fact_result (id_result PK, #id_evenement FK vers dim_evenement, #id_country FK vers dim_country,
             id_athlete, athlete_last_name, athlete_first_name,
             id_team, team_name, rank, performance_text, performance_value,
             source_id, created_at, updated_at)
</pre>

## Diagramme MLD

```mermaid
---
config:
  theme: base
  themeVariables:
    background: "#ffffff"
    primaryColor: "#ffffff"
    primaryTextColor: "#000000"
    secondaryColor: "#ffffff"
    tertiaryColor: "#ffffff"
    lineColor: "#000000"
    primaryBorderColor: "#000000"
    secondaryBorderColor: "#000000"
    tertiaryBorderColor: "#000000"
    mainBkg: "#ffffff"
    secondBkg: "#ffffff"
    textColor: "#000000"
  themeCSS: |
    .er .entityBox rect, .er .entityBox .attributeBoxEven, .er .entityBox .attributeBoxOdd { fill: #ffffff !important; stroke: #000000 !important; stroke-width: 3px !important; }
    .er .relationshipLine path { stroke: #000000 !important; stroke-width: 3px !important; fill: none !important; }
    .er .relationshipLabelBox { fill: #ffffff !important; stroke: #000000 !important; stroke-width: 2px !important; }
    .er .entityLabel { fill: #000000 !important; }
    .er .attributeText { fill: #000000 !important; }
---
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

    style dim_country fill:#ffffff,stroke:#000000,stroke-width:3px,color:#000000
    style dim_federation fill:#ffffff,stroke:#000000,stroke-width:3px,color:#000000
    style dim_sport fill:#ffffff,stroke:#000000,stroke-width:3px,color:#000000
    style dim_discipline fill:#ffffff,stroke:#000000,stroke-width:3px,color:#000000
    style dim_epreuve fill:#ffffff,stroke:#000000,stroke-width:3px,color:#000000
    style dim_edition fill:#ffffff,stroke:#000000,stroke-width:3px,color:#000000
    style dim_evenement fill:#ffffff,stroke:#000000,stroke-width:3px,color:#000000
    style fact_result fill:#ffffff,stroke:#000000,stroke-width:3px,color:#000000
```

## Règles de passage MCD vers MLD

1. Chaque entité devient une table relationnelle.
2. L'identifiant de chaque entité devient clé primaire (PK).
3. Associations (1,N) : la clé primaire du côté "1" migre comme FK dans la table du côté "N".
4. Pas d'association N:N dans ce modèle : pas de table associative nécessaire.
5. Attributs optionnels (athlete, team) : NULLable dans `fact_result` car certains résultats sont collectifs sans athlète nommé.
