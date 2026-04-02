# Procédure de tri et de gestion des données

> Projet : **Stream Score Stack** — Analyse des résultats olympiques.
> Conforme aux exigences C11 de l'épreuve E4.

---

## 1. Objectif

Définir les règles de **tri, nettoyage et qualification** des données à chaque étape du pipeline, garantissant la qualité et la traçabilité du dataset final.

---

## 2. Étapes du pipeline et règles de tri

### 2.1 Extraction (C8)

| Source          | Règle de tri appliquée                                    |
|-----------------|-----------------------------------------------------------|
| API REST        | Rejet des réponses HTTP ≠ 200 ; validation JSON schema   |
| Fichier CSV     | Vérification de l'encodage UTF-8 et du nombre de colonnes|
| HTML scraping   | Extraction uniquement des balises `<tr>` / `<td>` ciblées|
| PostgreSQL      | Requêtes avec `WHERE` pour exclure les enregistrements incomplets |
| Parquet/DuckDB  | Filtrage SQL natif sur les colonnes non-null              |

**Sortie** : fichiers CSV dans `data/staging/`, un par source.

### 2.2 Normalisation des colonnes (C10 — `normalize_columns.py`)

| Règle                              | Détail                                          |
|-------------------------------------|------------------------------------------------|
| Renommage standardisé              | Mapping explicite source → cible (COLUMN_MAPS) |
| Conversion de types                | Dates → `datetime`, booléens → `bool`, IDs → `int` |
| Nettoyage des chaînes              | `.strip()`, suppression espaces multiples       |

### 2.3 Nettoyage des enregistrements (C10 — `clean_records.py`)

| Règle                              | Détail                                          |
|-------------------------------------|------------------------------------------------|
| Suppression des nulls critiques    | Lignes sans clé primaire → supprimées           |
| Dédoublonnage                      | `drop_duplicates(subset=[pk])`, conserve la 1re occurrence |
| Validation des clés étrangères     | Enregistrements orphelins signalés dans les logs|

**Statistiques de nettoyage** : loguées et affichées dans le résumé du pipeline.

### 2.4 Fusion des sources (C10 — `merge_sources.py`)

| Règle                              | Détail                                          |
|-------------------------------------|------------------------------------------------|
| Priorité des sources               | API > Parquet > PostgreSQL (plus complet en premier)|
| Dédoublonnage multi-source         | `concat + drop_duplicates(subset=[pk], keep='first')` |
| Construction des dimensions        | Chaque dimension = table dédiée avec PK unique  |

### 2.5 Construction du dataset final (C10 — `build_final_dataset.py`)

| Règle                              | Détail                                          |
|-------------------------------------|------------------------------------------------|
| Alignement au schéma cible         | Seules les colonnes du DDL sont conservées      |
| Suppression des tables vides       | Tables sans données → non exportées             |
| Double format de sortie            | CSV (par table) + Parquet (dénormalisé)         |

---

## 3. Critères de qualité

| Critère              | Seuil acceptable       | Vérification                        |
|----------------------|------------------------|--------------------------------------|
| Complétude PK        | 100% non-null          | `clean_records.py` — nulls critiques |
| Unicité PK           | 0 doublons par table   | `drop_duplicates(subset=[pk])`       |
| Intégrité FK         | > 95% de correspondance| Vérifié à l'import PostgreSQL        |
| Cohérence de types   | 100% conforme au DDL   | `normalize_columns.py` + COPY        |
| Encodage             | UTF-8 exclusif         | Tous les `read_csv(encoding='utf-8')`|

---

## 4. Traçabilité

| Élément                | Emplacement                          |
|------------------------|--------------------------------------|
| Logs d'extraction      | Console stdout du pipeline           |
| Fichiers intermédiaires| `data/staging/*.csv`                 |
| Fichiers finaux        | `data/final/*.csv` + `.parquet`      |
| Statistiques nettoyage | Résumé dans `run_aggregation.py`     |
| Schéma DDL             | `sql/init_target_db.sql`             |
| Modèle MERISE          | `docs/merise_mcd.md`, `mld.md`, `mpd.md` |

---

## 5. Données exclues du traitement

| Type de donnée            | Raison de l'exclusion                     |
|---------------------------|-------------------------------------------|
| Données personnelles sensibles | Non présentes dans le dataset source  |
| Photos / médias           | Hors périmètre du projet                 |
| Données financières       | Non pertinentes pour l'analyse sportive   |
| Commentaires / texte libre| Non structurés, hors scope                |

---

## 6. Procédure de suppression

En cas de demande de suppression (art. 17 RGPD — droit à l'effacement) :

1. **Identifier** l'enregistrement concerné dans `fact_result` et/ou dimensions
2. **Supprimer** via SQL `DELETE FROM fact_result WHERE ...`
3. **Rejouer le pipeline** pour reconstruire les fichiers dérivés
4. **Documenter** la suppression dans un fichier `docs/deletions_log.md`

> **Note** : les données traitées étant publiques et historiques, les demandes d'effacement sont peu probables mais la procédure reste en place par conformité.
