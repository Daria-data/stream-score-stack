# E4 Livrable : Mise à disposition de flux de données

## E4 - Liste des compétences

- C8. Automatiser l’extraction de données
- C9. Développer des requêtes de type SQL d’extraction des données
- C10. Développer des règles d'agrégation de données issues de différentes sources
- C11. Créer une base de données
- C12. Partager le jeu de données

---

## 1 - Description détaillée de l'épreuve E4

Type d'épreuve : **Mise en situation professionnelle** (C8, C9, C10, C11, C12). Réel ou fictif.

Contexte de l'évaluation : Le projet évalué a pour but d’optimiser, d’automatiser, de pérenniser et de mettre à disposition les flux de données et les données, utiles et nécessaires à la réalisation du service numérique, par les équipes techniques (par exemple en analyse statistique, en business intelligence, en machine learning ou encore en intelligence artificielle).

**Tâches à réaliser par le candidat :** Optimiser, automatiser, pérenniser et mettre à disposition les flux de données utiles et nécessaires au projet.

**Livrables à fournir : Rapport professionnel (5-10 pages).**

Modalités de l'oral et Durée : **Présentation orale incluant une démonstration (15 minutes).** Correction du rapport professionnel. Soutenance orale individuelle.

---

## 2 - Description détaillée de chaque compétence et critères de validation officiels (référentiel BTS SIO)

### Compétence C8 : Automatiser l’extraction de données

Définition de la compétence : Automatiser l’extraction de données depuis un service web, une page web (scraping), un fichier de données, une base de données et un système big data en programmant le script adapté afin de pérenniser la collecte des données nécessaires au projet.

**Activités associées (Référentiel d'activités) :**

- Identification des contraintes techniques propres aux sources de données (consulter la documentation, les règles de confidentialité, etc.).
- Rédaction des spécifications techniques pour l’extraction des données.
- Construction les requêtes HTTP pour la récupération des données depuis un service web (REST).
- Lecture d’un fichier de données dans un script (Python, R, etc.).
- Téléchargement de l’HTML d’une ou plusieurs pages web visées par une action de scraping.
- Connexion programmatique (Python, R, etc.) à un système de gestion de base de données et à un système big data (Hive, Apache Impala, etc.).
- Programmation des filtrages/parsing des données utiles dans les résultats obtenus.

**Critères d'évaluation (référentiel officiel) :**

- La présentation du projet et de son contexte est complète : acteurs, objectifs fonctionnels et techniques, **environnements **et contraintes techniques, budget, organisation du travail et planification.
- Les spécifications techniques précisent : les technologies et outils, les services externes, les exigences de programmation (langages), l’accessibilité (disponibilité, accès).
- Le périmètre des spécifications techniques est complet : il couvre l’ensemble des moyens techniques à mettre en œuvre pour l’extraction et l'agrégation des données en un jeu de données brutes final.
- Le script d’extraction des données est fonctionnel : toutes les données visées sont effectivement récupérées à l’issue de l’exécution du script.
- Le script comprend un point de lancement, l’initialisation des dépendances et des connexions externes, les règles logiques de traitement, la gestion des erreurs et des exceptions, la fin du traitement et la sauvegarde des résultats.
- Le script d’extraction des données est versionné et accessible depuis un dépôt Git.
- **/!\ Alternative / Choix** : L’extraction des données est faite depuis un mix entre au moins les sources suivantes : un service web (API REST), un fichier de données, un scraping, une base de données et un système big data.

---

### Compétence C9 : Développer des requêtes de type SQL d’extraction des données

Définition de la compétence : Développer des requêtes de type SQL d’extraction des données depuis un système de gestion de base de données et un système big data en appliquant le langage de requête propre au système afin de préparer la collecte des données nécessaires au projet.

**Activités associées (Référentiel d'activités) :**

- Ecriture des requêtes d’extraction de type SQL de récupération de données stockées en base de données et depuis un système big data (Hive, Spark, etc).
- Exécution programmatique des requêtes d’extraction de type SQL.
- Exécution programmatique des requêtes d’extraction depuis un système big data.
- Documentation des requêtes d’extraction.

**Critères d'évaluation (référentiel officiel) :**

- Les requêtes de type SQL pour la collecte de données sont fonctionnelles : les données visées sont effectivement extraites suites à l'exécution des requêtes.
- La documentation des requêtes met en lumière le choix de sélections, filtrages, conditions, jointures, etc., en fonction des objectifs de collecte.
- La documentation explicite les optimisations appliquées aux requêtes.

---

### Compétence C10 : Développer des règles d'agrégation de données issues de différentes sources

Définition de la compétence : Développer des règles d'agrégation de données issues de différentes sources en programmant, sous forme de script, la suppression des entrées corrompues et en programmant l’homogénéisation des formats des données afin de préparer le stockage du jeu de données final.

**Activités associées (Référentiel d'activités) :**

- Rédaction des spécifications techniques pour l'agrégation des données.
- Programmation des règles d’agrégation des données collectées depuis chaque source en un jeu de données brutes unique.
- Programmation de l’identification des entrées corrompues dans le jeu de données (par exemple, données partielles et/ou manquantes) et de leur suppression.
- Programmation de la l’homogénéisation des formats de données (par exemple, format des dates, des unités, etc.).
- Versionnement des scripts avec Git et un dépôt Git en ligne.
- Documentation des scripts.

**Critères d'évaluation (référentiel officiel) :**

- Le script d’agrégation des données est fonctionnel : les données sont effectivement agrégées, nettoyées et normalisées en un seul jeu de données à l’issue de l’exécution du script.
- Le script d’agrégation des données est versionné et accessible depuis un dépôt Git.
- La documentation du script d’agrégation est complète : dépendances, commandes, les enchaînements logiques de l’algorithme, les choix de nettoyage et d’homogénéisation des formats données.

---

### Compétence C11 : Créer une base de données

Définition de la compétence : Créer une base de données dans le respect du RGPD en élaborant les modèles conceptuels et physiques des données à partir des données préparées et en programmant leur import afin de stocker le jeu de données du projet.

**Activités associées (Référentiel d'activités) :**

- Rédaction des spécifications techniques pour le stockage des données.
- Modélisation de la structure des données de la base de données selon la méthode MERISE.
- Choix du système de gestion de base de données.
- Création de la base de données dans le système de gestion de base de données.
- Rédaction ou mise à jour du registre des traitements de données personnelles en vue de la mise en conformité de la base de données avec le RGPD.
- Rédaction des procédures de tri des données personnelles stockées dans la base de données pour la mise en conformité avec le RGPD.
- Programmation du script d’import des données en base de données.

**Critères d'évaluation (référentiel officiel) :**

- Les modélisations des données respectent la méthode et le formalisme MERISE.
- **Le modèle physique** des données est fonctionnel : il est intégré avec succès lors de la création de la base de données, sans erreur.
- La base de données est choisie au regard de la modélisation des données et des contraintes du projet.
- La reproduction des procédures d’installation décrites (base de données et API) a pour résultat un système conforme aux objets techniques attendus.
- Le script d’import fourni est fonctionnel : il permet l’insertion des données dans le système mis en place.
- La documentation technique du script d’import est versionné à la racine du même dépôt Git que celui utilisé pour le script d’import.
- Le registre des traitements de données personnelles intègre l’ensemble des traitements de données personnelles impliqués dans la base de données.
- Les procédures de tri des données personnelles pour la mise en conformité de la base de données avec le RGPD sont rédigées.

---

### Compétence C12 : Partager le jeu de données

Définition de la compétence : Partager le jeu de données en configurant des interfaces logicielles et en créant des interfaces programmables afin de mettre à disposition le jeu de données pour le développement du projet.

**Activités associées (Référentiel d'activités) :**

- Rédaction des spécifications techniques des moyens de mise à disposition et d’accès aux données du projet : API (REST) et accès direct à la base de données.
- Développement des points de terminaison de l’API REST.
- Développement des règles d'autorisation et d’accès aux points de terminaison de l’API REST.
- Rédaction de la documentation technique de l’API REST.
- Configuration des accès à la base de données.

**Critères d'évaluation (référentiel officiel) :**

- La documentation technique de l’API (REST) couvre tous les points de terminaisons (end points).
- La documentation technique couvre les règles d’authentification et/ou d’autorisation de l’API.
- La documentation technique respecte les standards du modèle choisi (par exemple Open API).
- L’API REST est fonctionnelle pour l’accès aux données du projet : elle restreint par une autorisation (ou authentification) l'accès aux données.
- L’API REST est fonctionnelle pour la mise à disposition : elle permet la récupération de l’ensemble des données nécessaires au projet.
