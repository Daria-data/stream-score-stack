# Configuration des accès à la base de données

Ce document décrit **qui accède** à PostgreSQL, **avec quels droits** et
**par quel chemin réseau**, complément aux sections API auth
([e4_api_usage.md](e4_api_usage.md)) et RGPD
([registre_traitements_rgpd.md](registre_traitements_rgpd.md)).

Dans cette stack Docker, les services utilisent en pratique le **même compte PostgreSQL** (`postgres`) via les variables d’environnement. La **séparation des usages** (qui écrit, qui ne fait que lire) est donc assurée par le **comportement des applications** (requêtes `SELECT` vs `COPY` / pipeline), par le **découpage des conteneurs** et par le **réseau**, et non par des rôles SQL distincts au sein du SGBD. Des rôles dédiés (`readonly`, révocation d’`INSERT` hors loader) restent une **étape de durcissement** recommandée en production, hors périmètre technique détaillé ici.

---

## 1. Matrice des accès

| Rôle / Service | Conteneur | Droits DB | Schéma | Port réseau | Authentification |
|---------------|-----------|-----------|--------|-------------|------------------|
| **PostgreSQL** (SGBD) | `sports-pg` | superuser | `public` + `source` | `5432` interne, `5433` hôte | mot de passe via `POSTGRES_PASSWORD` |
| **Loader** | `sports-loader` | lecture CSV + écriture tables cibles | `public` | interne Docker | `DB_USER` / `DB_PASSWORD` env vars |
| **Streamlit** (app) | `sportquery-app` | **lecture seule** (SELECT) | `public` + `source` | interne Docker | `DB_USER` / `DB_PASSWORD` env vars |
| **API REST** | `sports-api` | **lecture seule** (SELECT) | `public` | interne Docker | `DB_USER` / `DB_PASSWORD` env vars |
| **Airflow** | `sports-airflow-*` | lecture/écriture (pipeline + métadonnées) | `public` + `source` | interne Docker | `SQL_ALCHEMY_CONN` env var |
| **Évaluateur / développeur** | hôte local | lecture via `psql` / DBeaver | tous | `localhost:5433` | `postgres` / `postgres` (défaut) |

---

## 2. Isolation réseau

```
                     ┌────────── sports-net (bridge) ──────────┐
                     │                                          │
  hôte:5433 ◄────── │  sports-pg :5432                          │
                     │    ▲   ▲   ▲   ▲                         │
                     │    │   │   │   └── airflow-scheduler     │
                     │    │   │   └────── sports-api             │
                     │    │   └────────── sportquery-app         │
                     │    └────────────── sports-loader          │
                     └──────────────────────────────────────────┘
```

- Tous les services communiquent sur le réseau Docker `sports-net`.
- Seul le port `5433` est exposé vers l'hôte (mappage `5433:5432`).
- Les services applicatifs utilisent `DB_HOST=postgres` et `DB_PORT=5432` (réseau interne).

---

## 3. Gestion des secrets

| Secret | Stockage | Valeur par défaut | Production |
|--------|----------|-------------------|------------|
| `DB_PASSWORD` | Variable d'environnement / `.env` | `postgres` | À remplacer par un mot de passe fort |
| `API_KEY` | Variable d'environnement / `.env` | `e4-demo-key-2026` | À remplacer, rotation recommandée |

Le fichier `.env` est listé dans `.gitignore` et **ne doit pas être commité**.

---

## 4. Principe du moindre privilège

Le tableau ci-dessous décrit le **niveau projet** (qui fait quoi), pas une matrice de **GRANT** PostgreSQL déjà déployée : c’est cohérent avec l’E4 et évite de surinterpréter la colonne « Droits DB ».

| Principe | Implémentation actuelle | Amélioration possible (hors scope E4) |
|----------|------------------------|---------------------------------------|
| Lecture seule pour les consommateurs | Streamlit et API n'exécutent que des `SELECT` | Créer un rôle PostgreSQL `readonly` dédié |
| Écriture limitée au loader | Seul `sports-loader` insère des données (`COPY`) | Révoquer `INSERT` pour les autres services |
| Données source en lecture seule | Volumes montés avec `:ro` | - |
| Pas d'accès direct au SGBD depuis Internet | Port 5433 exposé uniquement sur `localhost` | Firewall ou réseau privé en production |

---

## 5. Commandes de vérification rapide

```bash
# Vérifier la connectivité depuis l'hôte
psql -h localhost -p 5433 -U postgres -d sports -c "SELECT current_user, current_database();"

# Lister les tables accessibles
psql -h localhost -p 5433 -U postgres -d sports -c "\dt public.*"

# Vérifier le schéma source (legacy)
psql -h localhost -p 5433 -U postgres -d sports -c "\dt source.*"
```

---

Voir aussi : [e4_api_usage.md](e4_api_usage.md) pour l'authentification API,
[registre_traitements_rgpd.md](registre_traitements_rgpd.md) pour le registre des traitements.
