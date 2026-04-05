"""Split the original CSV into 5 distinct data sources.

Sources produced:
  1. data/mock_api/countries.json + sports.json  (for REST API source)
  2. data/html/editions.html                     (for scraping source)
  3. data/parquet/athletes_teams.parquet          (for DuckDB / big-data source)
  4. data/source_db/epreuves.csv + evenements.csv (for PostgreSQL source schema)

The original CSV (data/raw/fact_resultats_epreuves.csv) is kept as-is
and serves as source #5 — the file source (results / facts).

Usage:
    uv run python scripts/prepare_sources.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "raw" / "fact_resultats_epreuves.csv"


def _ensure_dirs() -> dict[str, Path]:
    """Create output directories and return a mapping of source names to paths."""
    dirs = {
        "mock_api": ROOT / "data" / "mock_api",
        "html": ROOT / "data" / "html",
        "parquet": ROOT / "data" / "parquet",
        "source_db": ROOT / "data" / "source_db",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def _load_raw() -> pd.DataFrame:
    """Load original CSV with proper encoding."""
    return pd.read_csv(RAW_CSV, encoding="utf-8")


# ── Source 1: Mock API data (countries + sports/disciplines) ─────────

def build_mock_api(df: pd.DataFrame, out: Path) -> None:
    """Extract unique countries and sports into JSON files."""
    countries = (
        df[["id_pays", "pays_en_base_resultats"]]
        .drop_duplicates()
        .rename(columns={"pays_en_base_resultats": "country_name"})
        .sort_values("id_pays")
    )
    countries_list = countries.to_dict(orient="records")
    (out / "countries.json").write_text(
        json.dumps(countries_list, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  countries.json: {len(countries_list)} records")

    sports = (
        df[["id_sport", "sport", "sport_en",
            "id_federation", "federation", "federation_nom_court"]]
        .drop_duplicates(subset=["id_sport"])
        .sort_values("id_sport")
    )
    sports_list = sports.to_dict(orient="records")
    (out / "sports.json").write_text(
        json.dumps(sports_list, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  sports.json: {len(sports_list)} records")


# ── Source 2: HTML page (editions) ───────────────────────────────────

def build_html_page(df: pd.DataFrame, out: Path) -> None:
    """Create an HTML page with a table of Olympic editions."""
    editions = (
        df[["id_edition", "edition_saison", "date_debut_edition",
            "date_fin_edition", "id_ville_edition", "edition_ville_en",
            "edition_nation_en", "type_competition"]]
        .drop_duplicates(subset=["id_edition"])
        .sort_values("date_debut_edition")
    )

    rows_html = ""
    for _, r in editions.iterrows():
        rows_html += (
            "      <tr>"
            f"<td>{r['id_edition']}</td>"
            f"<td>{r['edition_saison']}</td>"
            f"<td>{r['date_debut_edition']}</td>"
            f"<td>{r['date_fin_edition']}</td>"
            f"<td>{r['id_ville_edition']}</td>"
            f"<td>{r['edition_ville_en']}</td>"
            f"<td>{r['edition_nation_en']}</td>"
            f"<td>{r['type_competition']}</td>"
            "</tr>\n"
        )

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Olympic Editions</title></head>
<body>
<h1>Olympic Games Editions</h1>
<table id="editions" border="1">
  <thead>
    <tr>
      <th>id_edition</th><th>season</th><th>start_date</th>
      <th>end_date</th><th>id_city</th><th>city</th>
      <th>host_country</th><th>competition_type</th>
    </tr>
  </thead>
  <tbody>
{rows_html}  </tbody>
</table>
</body>
</html>"""

    (out / "editions.html").write_text(html, encoding="utf-8")
    print(f"  editions.html: {len(editions)} editions")


# ── Source 3: Parquet (athletes, teams, federations) ─────────────────

def build_parquet(df: pd.DataFrame, out: Path) -> None:
    """Save athletes/teams/federations as a Parquet file."""
    athletes = (
        df[["id_athlete_base_resultats", "athlete_nom", "athlete_prenom",
            "id_equipe", "equipe_en",
            "id_federation", "federation", "federation_nom_court"]]
        .copy()
    )
    # Keep rows where at least athlete or team info is present
    athletes = athletes.dropna(subset=["id_athlete_base_resultats", "id_equipe"], how="all")
    athletes = athletes.drop_duplicates()

    athletes.to_parquet(out / "athletes_teams.parquet", index=False, engine="pyarrow")
    print(f"  athletes_teams.parquet: {len(athletes)} records")


# ── Source 4: CSV for PostgreSQL source schema (epreuves, evenements) ─

def build_source_db_csv(df: pd.DataFrame, out: Path) -> None:
    """Extract épreuves and événements as CSV for the source DB schema."""
    epreuves = (
        df[["id_epreuve", "epreuve", "epreuve_genre", "epreuve_type",
            "est_epreuve_individuelle", "est_epreuve_olympique",
            "est_epreuve_ete", "est_epreuve_handi", "epreuve_sens_resultat",
            "id_discipline_administrative", "discipline_administrative",
            "id_specialite", "specialite", "id_sport"]]
        .drop_duplicates(subset=["id_epreuve"])
        .sort_values("id_epreuve")
    )
    epreuves.to_csv(out / "epreuves.csv", index=False, encoding="utf-8")
    print(f"  epreuves.csv: {len(epreuves)} records")

    evenements = (
        df[["id_evenement", "evenement", "evenement_en", "categorie_age",
            "id_epreuve", "id_edition"]]
        .drop_duplicates(subset=["id_evenement"])
        .sort_values("id_evenement")
    )
    evenements.to_csv(out / "evenements.csv", index=False, encoding="utf-8")
    print(f"  evenements.csv: {len(evenements)} records")


# ── Main ─────────────────────────────────────────────────────────────

def main() -> None:
    """Orchestrate source preparation."""
    print("Loading raw CSV...")
    df = _load_raw()
    print(f"  {len(df)} rows, {len(df.columns)} columns\n")

    dirs = _ensure_dirs()

    print("[Source 1] Mock API — countries + sports")
    build_mock_api(df, dirs["mock_api"])

    print("\n[Source 2] HTML — editions")
    build_html_page(df, dirs["html"])

    print("\n[Source 3] Parquet — athletes / teams / federations")
    build_parquet(df, dirs["parquet"])

    print("\n[Source 4] Source DB CSV — épreuves + événements")
    build_source_db_csv(df, dirs["source_db"])

    print("\n[Source 5] Original CSV kept as-is for file extraction")
    print(f"  {RAW_CSV.relative_to(ROOT)}")

    print("\nDone. All 5 sources ready.")


if __name__ == "__main__":
    main()
