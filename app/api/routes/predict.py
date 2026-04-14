import logging
import traceback

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.prediction import PredictionRequest, PredictionResponse
from app.core.database import get_db_optional
from app.core.metrics import PREDICTIONS_TOTAL, PREDICTION_LATENCY
from app.services.persistence_service import save_prediction
from app.services.prediction_service import predict

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
def predict_endpoint(request: PredictionRequest, db: Optional[Session] = Depends(get_db_optional)) -> PredictionResponse:
    with PREDICTION_LATENCY.labels(model_name=request.model_name).time():
        try:
            response = predict(request)
            if db is not None:
                try:
                    save_prediction(
                        db=db,
                        model_name=response.model_name,
                        input=request.input.model_dump(),
                        prediction=response.prediction.model_dump(),
                        probabilities=None,
                    )
                except Exception as db_err:
                    logger.warning("Persistance DB ignorée : %s", db_err)
            PREDICTIONS_TOTAL.labels(model_name=request.model_name, status="success").inc()
            return response
        except KeyError as e:
            PREDICTIONS_TOTAL.labels(model_name=request.model_name, status="not_found").inc()
            logger.error("Modèle introuvable : %s", e)
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            PREDICTIONS_TOTAL.labels(model_name=request.model_name, status="error").inc()
            logger.error("Erreur predict : %s\n%s", e, traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))
