"""
Chargement et fusion des données CSV + coordonnées géographiques (API gouv.fr).
"""
import csv
import json
import os
import urllib.request
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).parent / "data"))

_CRIME_COLS = [
    "Cambriolages_de_logement_nombre_sum",
    "Destructions_et_d_gradations_volontaires_nombre_sum",
    "Escroqueries_et_fraudes_aux_moyens_de_paiement_nombre_sum",
    "Trafic_de_stup_fiants_nombre_sum",
    "Usage_de_stup_fiants_nombre_sum",
    "Usage_de_stup_fiants_AFD__nombre_sum",
    "Violences_physiques_hors_cadre_familial_nombre_sum",
    "Violences_physiques_intrafamiliales_nombre_sum",
    "Violences_sexuelles_nombre_sum",
    "Vols_avec_armes_nombre_sum",
    "Vols_d_accessoires_sur_v_hicules_nombre_sum",
    "Vols_dans_les_v_hicules_nombre_sum",
    "Vols_de_v_hicule_nombre_sum",
    "Vols_sans_violence_contre_des_personnes_nombre_sum",
    "Vols_violents_sans_arme_nombre_sum",
]

TENDENCY_LABELS = {
    "extreme-gauche": "Extrême gauche",
    "gauche": "Gauche",
    "centre": "Centre",
    "droite": "Droite",
    "extreme-droite": "Extrême droite",
}


def _safe_float(val, default: float = 0.0) -> float:
    try:
        return float(str(val).replace(",", ".").strip())
    except (ValueError, TypeError):
        return default


def _normalize_code(code: str) -> str:
    """'33001.0' → '33001'"""
    try:
        return str(int(float(code)))
    except (ValueError, TypeError):
        return str(code).strip()


def _load_targets() -> dict:
    path = DATA_DIR / "Table_TARGETS (1).csv"
    result: dict = {}
    seen: set = set()
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = _normalize_code(row["Code_commune"])
            if code in seen:
                continue
            seen.add(code)

            inscrits = _safe_float(row["Inscrits_22"])
            abstentions = _safe_float(row["Abstentions_22"])
            exprimes = _safe_float(row["Exprimes_22"])

            votes = {
                "extreme-gauche": _safe_float(row["Votes_Extreme_Gauche"]),
                "gauche": _safe_float(row["Votes_Gauche"]),
                "centre": _safe_float(row["Votes_Centre"]),
                "droite": _safe_float(row["Votes_Droite"]),
                "extreme-droite": _safe_float(row["Votes_Extreme_Droite"]),
            }

            participation = (
                (inscrits - abstentions) / inscrits * 100 if inscrits > 0 else 0.0
            )

            dominant = max(votes, key=votes.get) if exprimes > 0 else None

            result[code] = {
                "name": row["Libelle_de_la_commune"],
                "inscrits": inscrits,
                "abstentions": abstentions,
                "exprimes": exprimes,
                "votes": votes,
                "participation": round(participation, 1),
                "tendance_key": dominant,
            }
    return result


def _load_features() -> dict:
    path = DATA_DIR / "Table_FEATURES_FINAL.csv"
    result: dict = {}
    seen: set = set()
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = _normalize_code(row["Code_commune"])
            if code in seen:
                continue
            seen.add(code)

            population = _safe_float(
                row.get("Nombre_de_personnes_dans_les_menages_fiscaux", 0)
            )
            median_annual = _safe_float(row.get("Mediane_du_niveau_vie", 0))
            age_moyen = _safe_float(row.get("age_moyen", 0))
            # Proxy du chômage : part des revenus issus des indemnités chômage
            chomage_part = _safe_float(
                row.get("dont_part_des_indemnites_de_chomage", 0)
            )

            # Niveau d'éducation : % avec Bac+2 ou plus
            sup_court = _safe_float(row.get("Sup_Court_Bac_plus_2", 0))
            sup_long34 = _safe_float(row.get("Sup_Long_Bac_plus_3_4", 0))
            sup_long5 = _safe_float(row.get("Sup_Long_Bac_plus_5", 0))
            total_sup = sup_court + sup_long34 + sup_long5
            sans_diplome = _safe_float(row.get("Sans_Diplome_CEP", 0))
            brevet = _safe_float(row.get("Brevet", 0))
            cap_bep = _safe_float(row.get("CAP_BEP", 0))
            bac = _safe_float(row.get("Bac", 0))
            total_edu = sans_diplome + brevet + cap_bep + bac + total_sup
            pct_sup = (total_sup / total_edu * 100) if total_edu > 0 else 0.0

            if pct_sup >= 35:
                edu_level = "high"
            elif pct_sup >= 20:
                edu_level = "medium"
            else:
                edu_level = "low"

            total_crimes = sum(_safe_float(row.get(c, 0)) for c in _CRIME_COLS)
            crime_rate = (
                total_crimes / population * 1000 if population > 0 else 0.0
            )

            result[code] = {
                "population": int(population),
                "averageSalary": round(median_annual / 12),
                "averageAge": round(age_moyen, 1),
                "unemploymentRate": round(chomage_part, 1),
                "educationLevel": edu_level,
                "crimeRate": round(crime_rate, 2),
            }
    return result


def _fetch_geo(departement: str = "33") -> dict:
    """Récupère les centroïdes des communes via l'API geo.api.gouv.fr."""
    url = (
        f"https://geo.api.gouv.fr/communes"
        f"?codeDepartement={departement}&fields=code,nom,centre&format=json"
    )
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        result = {}
        for item in data:
            code = item["code"]
            centre = item.get("centre") or {}
            coords = centre.get("coordinates", [None, None])
            result[code] = {"lon": coords[0], "lat": coords[1]}
        return result
    except Exception as exc:
        print(f"[data_loader] Impossible de récupérer les coordonnées geo : {exc}")
        return {}


def _build_tendance_label(votes: dict) -> str:
    if not votes or all(v == 0 for v in votes.values()):
        return "Inconnu"
    dominant = max(votes, key=votes.get)
    return TENDENCY_LABELS.get(dominant, dominant)


def load_all(departement: str = "33") -> list[dict]:
    """Charge et fusionne toutes les données. Retourne la liste des communes."""
    targets = _load_targets()
    features = _load_features()
    geo = _fetch_geo(departement)

    cities: list[dict] = []
    for code, t in targets.items():
        f = features.get(code, {})
        g = geo.get(code, {"lon": None, "lat": None})

        exprimes = t["exprimes"]
        votes = t["votes"]

        vote_shares = {
            k: round(v / exprimes * 100, 1) if exprimes > 0 else 0.0
            for k, v in votes.items()
        }

        try:
            city_id = int(code)
        except ValueError:
            city_id = 0

        cities.append(
            {
                "id": city_id,
                "code": code,
                "name": t["name"],
                "lon": g.get("lon"),
                "lat": g.get("lat"),
                "population": f.get("population", 0),
                "participation": t["participation"],
                "tendance": _build_tendance_label(votes),
                "tendance_key": t["tendance_key"],
                "socioEconomique": {
                    "unemploymentRate": f.get("unemploymentRate", 0),
                    "crimeRate": f.get("crimeRate", 0),
                    "averageAge": f.get("averageAge", 0),
                    "educationLevel": f.get("educationLevel", "medium"),
                    "averageSalary": f.get("averageSalary", 0),
                },
                "resultats": [
                    {"key": k, "value": vote_shares[k]}
                    for k in [
                        "extreme-gauche",
                        "gauche",
                        "centre",
                        "droite",
                        "extreme-droite",
                    ]
                ],
                # Agrégats bruts utiles pour /api/results
                "_inscrits": t["inscrits"],
                "_abstentions": t["abstentions"],
                "_exprimes": exprimes,
                "_votes_raw": votes,
            }
        )

    return cities
