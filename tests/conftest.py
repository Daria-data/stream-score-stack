"""Shared fixtures for the test suite."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture()
def sample_api_countries() -> pd.DataFrame:
    """Sample country reference from the API source."""
    return pd.DataFrame({
        "id_pays": [1, 2, 3],
        "country_name": ["France", "Germany", "Japan"],
    })


@pytest.fixture()
def sample_pg_epreuves() -> pd.DataFrame:
    """Sample épreuves extract from PostgreSQL source."""
    return pd.DataFrame({
        "id_epreuve": [10, 20],
        "epreuve": ["100m Hommes", "Marathon Femmes"],
        "epreuve_genre": ["Hommes", "Femmes"],
        "epreuve_type": ["Individuel", "Individuel"],
        "est_epreuve_individuelle": [1, 1],
        "est_epreuve_olympique": [1, 1],
        "est_epreuve_ete": [1, 1],
        "est_epreuve_handi": [0, 0],
        "epreuve_sens_resultat": [0, 0],
        "id_discipline_administrative": [251, 251],
        "discipline_administrative": ["Athlétisme", "Athlétisme"],
        "id_specialite": [300, 301],
        "specialite": ["Sprint", "Fond"],
        "id_sport": [37, 37],
    })


@pytest.fixture()
def sample_file_results() -> pd.DataFrame:
    """Sample results CSV rows."""
    return pd.DataFrame({
        "id_resultat": [100, 200, 300],
        "id_resultat_source": [None, None, None],
        "source": ["file", "file", "file"],
        "id_athlete_base_resultats": [1, 2, 3],
        "id_personne": [None, None, None],
        "athlete_nom": ["Bolt", "Kipchoge", "Unknown"],
        "athlete_prenom": ["Usain", "Eliud", "X"],
        "id_equipe": [None, None, None],
        "equipe_en": [None, None, None],
        "id_pays": [1, 2, 999],
        "id_epreuve": [10, 20, 10],
        "id_evenement": [500, 600, 500],
        "id_edition": [1, 1, 1],
        "classement_epreuve": [1, 1, None],
        "performance_finale_texte": ["9.58", "2:01:39", None],
        "performance_finale": [9.58, 7299.0, None],
        "dt_creation": [None, None, None],
        "dt_modification": [None, None, None],
    })
