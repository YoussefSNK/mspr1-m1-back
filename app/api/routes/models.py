from fastapi import APIRouter

from app.services.model_registry import list_models

router = APIRouter()


@router.get("/models")
def get_models() -> list[str]:
    return list_models()
