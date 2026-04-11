from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app
from starlette.routing import Mount

from app.api.router import api_router
from app.core.database import Base, engine
from app.models import prediction  # noqa: F401 — enregistre le modèle auprès de Base
from app.services.model_registry import load_all_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    load_all_models()
    yield


app = FastAPI(lifespan=lifespan, routes=[Mount("/metrics", make_asgi_app())])

app.include_router(api_router)
