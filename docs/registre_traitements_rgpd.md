# Registre des traitements : RGPD

> Document conforme à l'article 30 du RGPD.
> Projet : **OlympScore** : analyse des résultats olympiques.

---

## 1. Responsable du traitement

| Champ                  | Valeur                                         |
|------------------------|-------------------------------------------------|
| Organisation           | OlympScore            |
| Responsable            | Daria Antipova                                  |
| Contact DPO            |08 86 888 92 teams, email: daria.antipova@gmail.com     |

---

## 2. Finalité du traitement

| Finalité | Base légale | Description |
|----------|-------------|-------------|
| Analyse statistique des données sportives publiques et production d’un livrable technique traçable | Intérêt légitime (art. 6.1.f) | Agrégation et visualisation de résultats olympiques issus de sources ouvertes. Le traitement inclut la documentation, les contrôles qualité et la reproductibilité du pipeline nécessaires au livrable. Le cadre de formation et les destinataires associés sont précisés au §6. |

---

## 3. Catégories de données traitées

| Catégorie                | Données concernées                              | Sensibilité |
|--------------------------|-------------------------------------------------|-------------|
| Identité sportive        | Nom, prénom d'athlètes (publics)               | Faible      |
| Résultats sportifs       | Classement, performance, médaille              | Faible      |
| Référentiels géo         | Pays, ville d'édition                          | Non sensible|
| Référentiels sportifs    | Sport, discipline, épreuve, fédération         | Non sensible|
| Métadonnées techniques   | Timestamps (created_at, updated_at), source_id | Non sensible|

### Données sensibles (art. 9 RGPD)

**Aucune donnée sensible n'est traitée** dans ce projet :
- Pas de données de santé
- Pas d'opinions politiques ou religieuses
- Pas de données biométriques
- Pas de données relatives aux mineurs (pas d'âge collecté)

---

## 4. Catégories de personnes concernées

| Catégorie           | Volume estimé  | Détail                                      |
|---------------------|----------------|----------------------------------------------|
| Athlètes olympiques | ~18 000        | Noms/prénoms publics issus de données ouvertes|

---

## 5. Sources des données

| Source                     | Type           | Accès          | Licence / Statut       |
|----------------------------|----------------|----------------|------------------------|
| CSV brut (fact_resultats)  | Fichier        | Local          | Données publiques      |
| Mock API (FastAPI)         | API REST       | Interne Docker | Généré depuis CSV      |
| PostgreSQL (source schema) | Base de données| Docker interne | Données publiques      |
| HTML (editions)            | Web scraping   | Fichier local  | Données publiques      |
| Parquet (athletes/teams)   | Big data       | Fichier local  | Données publiques      |

---

## 6. Destinataires des données

| Destinataire       | Accès          | Justification                     |
|--------------------|----------------|-----------------------------------|
| Évaluateurs (formation) | Lecture seule | Évaluation pédagogique du livrable |
| Responsable du traitement (cf. §1) | Lecture/écriture | Développement, exploitation locale et maintenance du dispositif |
| API REST (endpoints protégés) | Lecture seule  | Consultation via authentification par clé API |

---

## 7. Transferts hors UE

**Aucun transfert hors UE.** Toutes les données sont traitées localement (machine de développement) ou dans des conteneurs Docker sur infrastructure locale.

---

## 8. Durée de conservation

| Données               | Durée                     | Justification               |
|------------------------|---------------------------|-----------------------------|
| Données brutes (CSV)  | Durée du projet + 1 an   | Besoin de reproductibilité  |
| Base PostgreSQL        | Session Docker            | Reconstruit à chaque deploy |
| Fichiers staging/final | Durée du projet           | Intermédiaires de pipeline  |
| Logs applicatifs       | 30 jours                 | Debugging et audit          |

---

## 9. Mesures de sécurité (art. 32 RGPD)

| Mesure                        | Implémentation                                     |
|-------------------------------|-----------------------------------------------------|
| Authentification DB           | Mot de passe PostgreSQL via variable d'environnement|
| Authentification API          | API key via en-tête HTTP (`X-API-Key`)              |
| Chiffrement en transit        | Réseau Docker interne isolé                         |
| Contrôle d'accès              | Volumes montés en lecture seule (:ro)               |
| Séparation des environnements | Docker Compose isole chaque service                 |
| Journalisation                | Logs d'extraction avec timestamps                   |

---

## 10. Analyse d'impact (AIPD)

Une AIPD complète **n'est pas requise** car :
- Les données traitées sont **exclusivement publiques**
- Aucun profilage ni scoring d'individus
- Aucune prise de décision automatisée affectant des personnes
- Volume limité (~35 000 résultats, ~18 000 athlètes)
- Pas de croisement avec d'autres bases de données personnelles
