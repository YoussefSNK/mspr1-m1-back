from typing import Any

from pydantic import BaseModel

# todo : faudra changer ça quand on saura le modèle il prend quoi et répond quoi

class PredictionRequest(BaseModel):
    model_name: str
    input: Any


class PredictionResponse(BaseModel):
    model_name: str
    prediction: Any
    probabilities: Any | None = None
