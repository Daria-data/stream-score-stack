import pandas as pd

df = pd.read_csv("data/raw/fact_resultats_epreuves.csv", encoding="utf-8")
print("Shape:", df.shape)
print()
print("=== CARDINALITIES ===")
groups = {
    "Countries": "id_pays",
    "Sports": "id_sport",
    "Disciplines": "id_discipline_administrative",
    "Specialites": "id_specialite",
    "Epreuves": "id_epreuve",
    "Evenements": "id_evenement",
    "Editions": "id_edition",
    "Athletes": "id_athlete_base_resultats",
    "Equipes": "id_equipe",
    "Federations": "id_federation",
    "Villes": "id_ville_edition",
    "Results": "id_resultat",
}
for name, c in groups.items():
    nuniq = df[c].nunique()
    nnull = df[c].isna().sum()
    nstr_null = (df[c].astype(str) == "NULL").sum()
    print(f"  {name:20} ({c}): {nuniq} unique, {nnull} NaN, {nstr_null} str-NULL")

print()
print("=== COUNTRY samples ===")
sub = df[["id_pays", "pays_en_base_resultats"]].drop_duplicates().sort_values("id_pays")
print(f"  {len(sub)} unique")
print(sub.head(5).to_string(index=False))

print()
print("=== SPORT > DISCIPLINE > SPECIALITE hierarchy ===")
cols_s = ["id_sport", "sport_en", "id_discipline_administrative", "discipline_administrative", "id_specialite", "specialite"]
sub2 = df[cols_s].drop_duplicates()
n_sport = sub2["id_sport"].nunique()
n_disc = sub2["id_discipline_administrative"].nunique()
n_spec = sub2["id_specialite"].nunique()
print(f"  {n_sport} sports, {n_disc} disciplines, {n_spec} specialites")

print()
print("=== EDITION samples ===")
cols_e = ["id_edition", "edition_saison", "date_debut_edition", "date_fin_edition",
          "id_ville_edition", "edition_ville_en", "edition_nation_en", "type_competition"]
sub3 = df[cols_e].drop_duplicates().sort_values("date_debut_edition")
print(f"  {len(sub3)} unique editions")
print(sub3.head(5).to_string(index=False))

print()
print("=== ATHLETE nulls ===")
print(f"  athlete_nom NaN: {df['athlete_nom'].isna().sum()} / {len(df)}")
print(f"  id_personne str-NULL: {(df['id_personne'].astype(str) == 'NULL').sum()}")
print(f"  id_athlete str-NULL: {(df['id_athlete_base_resultats'].astype(str) == 'NULL').sum()}")

print()
print("=== EPREUVE flags ===")
for c in ["est_epreuve_individuelle", "est_epreuve_olympique", "est_epreuve_ete", "est_epreuve_handi"]:
    print(f"  {c}: {df[c].value_counts().to_dict()}")

print()
print("=== type_competition ===")
print(df["type_competition"].value_counts().to_dict())

print()
print("=== edition_saison ===")
print(df["edition_saison"].value_counts().to_dict())

print()
print("=== epreuve_genre ===")
print(df["epreuve_genre"].value_counts().to_dict())

print()
print("=== epreuve_type ===")
print(df["epreuve_type"].value_counts().to_dict())

print()
print("=== FEDERATION samples ===")
sub4 = df[["id_federation", "federation", "federation_nom_court"]].drop_duplicates()
print(f"  {len(sub4)} unique federations")
print(sub4.head(5).to_string(index=False))
