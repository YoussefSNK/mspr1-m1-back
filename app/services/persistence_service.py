import numpy as np
from sqlalchemy.orm import Session

from app.models.prediction import Prediction


def _to_jsonable(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def save_prediction(
    db: Session,
    model_name: str,
    input: object,
    prediction: object,
    probabilities: object | None,
) -> Prediction:
    record = Prediction(
        model_name=model_name,
        input=_to_jsonable(input),
        prediction=_to_jsonable(prediction),
        probabilities=_to_jsonable(probabilities),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
