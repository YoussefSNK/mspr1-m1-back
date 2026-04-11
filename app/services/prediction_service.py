import numpy as np

from app.api.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.model_registry import get_model


def predict(request: PredictionRequest) -> PredictionResponse:
    model = get_model(request.model_name)
    # todo : ici aussi faudra changer pour le modèle dcp
    X = np.array([request.input]) if not isinstance(request.input, list) else np.array(request.input)

    prediction = model.predict(X)
    result = prediction[0] if hasattr(prediction, "__len__") else prediction

    probabilities = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        classes = model.classes_ if hasattr(model, "classes_") else range(len(proba))
        probabilities = {str(cls): float(p) for cls, p in zip(classes, proba)}

    return PredictionResponse(
        model_name=request.model_name,
        prediction=result,
        probabilities=probabilities,
    )
