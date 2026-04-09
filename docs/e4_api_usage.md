# Guide d'utilisation de l'API E4 (C12)

Ce document explique comment démarrer et utiliser la couche API REST du projet.

## 1) Vue d'ensemble du service

- URL de base : `http://localhost:8888`
- Documentation OpenAPI : `http://localhost:8888/docs`
- ReDoc : `http://localhost:8888/redoc`
- Authentification : en-tête `X-API-Key`, clé `e4-demo-key-2026`

## 2) Démarrer la stack

Depuis la racine du dépôt :

```bash
docker compose up -d --build
docker compose ps
```

État attendu :
- `sports-api` en `Up (healthy)`
- `sports-pg` en `Up (healthy)`
- `sports-loader` terminé avec succès (`Exited (0)`)

## 3) Modèle d'authentification

L'API utilise une stratégie simple par clé API :

- Nom de l'en-tête : `X-API-Key`
- Clé absente -> `401 Unauthorized`
- Clé invalide -> `403 Forbidden`

L'endpoint de santé est public et ne nécessite pas d'authentification.

> **Note de sécurité.** La clé `e4-demo-key-2026` est un repli de démonstration. En production, utiliser une clé secrète gérée hors dépôt.

## 4) Endpoints

### Endpoint public

- `GET /health`

### Endpoints protégés (nécessitent `X-API-Key`)

- `GET /countries`
- `GET /countries/{country_id}`
- `GET /sports`
- `GET /federations`
- `GET /editions`
- `GET /results`
- `GET /results/{result_id}`
- `GET /stats/results-by-country`

## 5) Requêtes de démo (copier-coller)

### Vérification de santé

```bash
curl -s http://localhost:8888/health
```

### Pays (5 premiers)

```bash
curl -s "http://localhost:8888/countries?limit=5" \
  -H "X-API-Key: e4-demo-key-2026"
```

### Sports (5 premiers)

```bash
curl -s "http://localhost:8888/sports?limit=5" \
  -H "X-API-Key: e4-demo-key-2026"
```

### Résultats paginés

```bash
curl -s "http://localhost:8888/results?page=1&page_size=10" \
  -H "X-API-Key: e4-demo-key-2026"
```

### Résultats filtrés par pays

```bash
curl -s "http://localhost:8888/results?page=1&page_size=10&country_id=46" \
  -H "X-API-Key: e4-demo-key-2026"
```

### Détail d'un résultat

```bash
curl -s "http://localhost:8888/results/6045706" \
  -H "X-API-Key: e4-demo-key-2026"
```

### Top pays par nombre de résultats

```bash
curl -s "http://localhost:8888/stats/results-by-country?limit=10" \
  -H "X-API-Key: e4-demo-key-2026"
```

### Test d'échec d'authentification (401 attendu)

```bash
curl -i "http://localhost:8888/countries"
```

## 6) Parcours de démonstration Swagger (pas-à-pas)

1. Ouvrir `http://localhost:8888/docs`
2. Exécuter `GET /health`
3. Ouvrir un endpoint protégé (par exemple `GET /countries`)
4. Cliquer sur "Try it out"
5. Ajouter l'en-tête `X-API-Key` avec la valeur `e4-demo-key-2026`
6. Exécuter et vérifier la réponse JSON
7. Montrer la pagination sur `GET /results`
8. Montrer l'endpoint d'agrégation `GET /stats/results-by-country`

## 7) Dépannage

- Si `sports-api` n'est pas healthy :
  - `docker logs sports-api`
- Si l'API retourne des erreurs de connexion DB :
  - vérifier que `sports-pg` est healthy
  - vérifier que `sports-loader` est terminé avec succès
- Si les tables sont vides :
  - relancer la stack avec reset complet :

```bash
docker compose down -v
docker compose up -d --build
```

