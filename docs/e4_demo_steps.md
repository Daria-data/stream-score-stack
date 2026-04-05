# E4 — Scénario de démonstration (jury)

Durée indicative : **8–12 minutes**. Adapter le niveau de détail au temps imparti.

---

## Avant la démo

1. Démarrer Docker Desktop.  
2. À la racine du projet : `docker compose up -d --build`  
3. Attendre que `sports-loader` soit **Exited (0)** et que `sports-api` soit **healthy** (`docker compose ps`).  
4. Ouvrir dans l’ordre (onglets du navigateur) :  
   - http://localhost:8501 — Streamlit  
   - http://localhost:8888/docs — API  
   - http://localhost:8080 — Airflow (`admin` / `admin`)

---

## 1. Positionnement (30 s)

**À dire** : projet de plateforme données sur les résultats olympiques ; chaîne complète **multi-sources → SQL → agrégation → BDD normalisée → API + interface SQL** ; compétences **C8 à C12** ; orchestration **Airflow**.

**À montrer** : schéma dans `README.md` ou `README_E4.md` (optionnel, écran partagé).

---

## 2. Architecture données (1–2 min)

**À dire** : plusieurs types de sources (fichier, API, HTML, PostgreSQL *source*, Parquet/DuckDB) ; staging puis dataset final ; schéma en **étoile / flocon** (7 dimensions + fait).

**À montrer** (au choix) :

- Dossiers `data/staging/` et `data/final/` dans l’IDE, ou  
- Table des métriques dans la **sidebar Streamlit** (comptes par table).

---

## 3. Base de données et MERISE (1–2 min)

**À dire** : modélisation **MERISE** (MCD / MLD / MPD) dans `docs/` ; schéma physique `sql/init_target_db.sql` ; conformité **RGPD** (registre + procédure) pour C11.

**À montrer** : ouvrir un fichier `docs/merise_mcd.md` (aperçu Mermaid) ou le PDF/export si le jury le demande.

---

## 4. Requêtes SQL (C9) — 2 min

**À dire** : requêtes documentées dans `sql/extraction/` ; exécution programmatique `run_sql_extraction` ; variantes Postgres + DuckDB.

**À montrer** :

- Streamlit : charger un modèle du type **« C9: … (source) »** ou une requête analytique sur `dim_*` / `fact_result`, cliquer **Run query**, montrer le résultat.  
- Ou ouvrir `docs/e4_sql_documentation.md` et pointer la requête correspondante.

---

## 5. Interface SQL (Streamlit) — 1 min

**À dire** : playground pour interroger la **BDD cible** (pas seulement le CSV brut).

**À montrer** : template **Top 10 countries** ou **Results by edition** ; export CSV/Excel si pertinent.

---

## 6. API REST (C12) — 2–3 min

**À dire** : exposition des données via **FastAPI** ; authentification par **clé API** ; documentation **OpenAPI** auto-générée.

**À montrer** :

1. http://localhost:8888/docs  
2. **Authorize** (icône cadenas) : `X-API-Key` = valeur par défaut du projet (voir `docs/e4_api_usage.md`).  
3. `GET /health` (sans clé).  
4. `GET /countries` ou `GET /stats/results-by-country` (avec clé).  

Optionnel : montrer un `curl` depuis `docs/e4_api_usage.md`.

---

## 7. Orchestration Airflow — 1–2 min

**À dire** : DAG `e4_pipeline` enchaîne extract → SQL → agrégation → import ; déclenchement manuel pour la démo, planifiable en production.

**À montrer** : liste des DAGs → `e4_pipeline` → graphe des 4 tâches ; un run **success** récent (logs si question).

---

## 8. Synthèse et questions (1 min)

**À dire** : traçabilité des étapes, données reproductibles (`docker compose down -v` puis `up`), documentation centralisée (`README_E4.md` + `docs/e4_*.md`).

**Anticiper** : pourquoi plusieurs `id_edition` pour une même édition « métier » → clés techniques vs clés métier ; groupements par année / ville / type dans les requêtes adaptées.

---

## Check-list rapide

| Élément | OK |
|---------|-----|
| Docker `ps` — services up | ☐ |
| Streamlit affiche des lignes | ☐ |
| `/docs` API + clé API | ☐ |
| DAG `e4_pipeline` visible | ☐ |
| `README_E4.md` + liens docs | ☐ |

---

*Pour le détail des commandes et ports : [e4_installation.md](e4_installation.md).*
