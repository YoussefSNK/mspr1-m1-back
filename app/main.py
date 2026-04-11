from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.services.model_registry import load_all_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_all_models()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(api_router)
