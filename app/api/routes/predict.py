from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.prediction import PredictionRequest, PredictionResponse
from app.core.database import get_db
from app.core.metrics import PREDICTIONS_TOTAL, PREDICTION_LATENCY
from app.services.persistence_service import save_prediction
from app.services.prediction_service import predict

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
def predict_endpoint(request: PredictionRequest, db: Session = Depends(get_db)) -> PredictionResponse:
    with PREDICTION_LATENCY.labels(model_name=request.model_name).time():
        try:
            response = predict(request)
            save_prediction(
                db=db,
                model_name=response.model_name,
                input=request.input,
                prediction=response.prediction,
                probabilities=response.probabilities,
            )
            PREDICTIONS_TOTAL.labels(model_name=request.model_name, status="success").inc()
            return response
        except KeyError as e:
            PREDICTIONS_TOTAL.labels(model_name=request.model_name, status="not_found").inc()
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            PREDICTIONS_TOTAL.labels(model_name=request.model_name, status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))
