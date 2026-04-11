from fastapi import APIRouter, HTTPException

from app.api.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction_service import predict

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
def predict_endpoint(request: PredictionRequest) -> PredictionResponse:
    try:
        return predict(request)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
