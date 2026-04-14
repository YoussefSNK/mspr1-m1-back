import numpy as np

from app.api.schemas.prediction import ElectionPrediction, PredictionRequest, PredictionResponse
from app.services.model_registry import get_model

FEATURE_ORDER = [
    "FEAT_Vote_2017",
    "Mediane_du_niveau_vie",
    "part_ouvrier",
    "part_cadre",
    "part_retraite_csp",
    "Cambriolages_de_logement_nombre_sum",
    "Violences_physiques_hors_cadre_familial_nombre_sum",
    "age_moyen",
    "Sans_Diplome_CEP",
]

OUTPUT_LABELS = ["extreme_gauche", "gauche", "centre", "droite", "extreme_droite"]


def predict(request: PredictionRequest) -> PredictionResponse:
    model = get_model(request.model_name)
    imputer = get_model("imputer_electio")
    scaler = get_model("scaler_electio")

    raw = request.input.model_dump()
    X = np.array([[raw[f] for f in FEATURE_ORDER]], dtype=float)

    X = imputer.transform(X)
    X = scaler.transform(X)

    output = model.predict(X)[0]

    prediction = ElectionPrediction(**{
        label: round(float(val), 2)
        for label, val in zip(OUTPUT_LABELS, output)
    })

    return PredictionResponse(
        model_name=request.model_name,
        prediction=prediction,
    )
