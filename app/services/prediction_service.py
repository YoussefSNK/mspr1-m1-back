import math

import pandas as pd

from app.api.schemas.prediction import ElectionPrediction, PredictionRequest, PredictionResponse
from app.services.model_registry import get_model

FEATURE_ORDER = [
    "Part_des_revenus_du_patrimoine_et_autres_revenus",
    "Part_des_impots",
    "Part_des_menages_fiscaux_imposes",
    "9e_decile_du_niveau_de_vie_",
    "Rapport_interdecile_9e_decile/1er_decile",
    "dont_part_des_revenus_des_activites_non_salariees",
    "Mediane_du_niveau_vie",
    "dont_part_des_prestations_familiales",
    "dont_part_des_indemnites_de_chomage",
    "Part_des_pensions_retraites_et_rentes",
    "age_moyen",
    "part_cadre",
    "part_ouvrier",
    "log_taille_commune",
]

# Champs de ElectionInput dont le nom diffère de la feature attendue par le modèle
FIELD_TO_FEATURE = {
    "decile_9_niveau_de_vie": "9e_decile_du_niveau_de_vie_",
    "rapport_interdecile_d9_d1": "Rapport_interdecile_9e_decile/1er_decile",
}

OUTPUT_LABELS = ["extreme_gauche", "gauche", "centre", "droite", "extreme_droite"]


def predict(request: PredictionRequest) -> PredictionResponse:
    model = get_model(request.model_name)
    imputer = get_model("imputer_electio")
    scaler = get_model("scaler_electio")

    raw = request.input.model_dump()

    taille = raw.pop("nombre_personnes_menages_fiscaux")
    raw["log_taille_commune"] = math.log(taille) if taille and taille > 0 else None

    for field_name, feature_name in FIELD_TO_FEATURE.items():
        raw[feature_name] = raw.pop(field_name)

    X = pd.DataFrame([[raw[f] for f in FEATURE_ORDER]], columns=FEATURE_ORDER)

    X = pd.DataFrame(imputer.transform(X), columns=FEATURE_ORDER)
    X = pd.DataFrame(scaler.transform(X), columns=FEATURE_ORDER)

    output = model.predict(X)[0]

    prediction = ElectionPrediction(**{
        label: round(float(val), 2)
        for label, val in zip(OUTPUT_LABELS, output)
    })

    return PredictionResponse(
        model_name=request.model_name,
        prediction=prediction,
    )
