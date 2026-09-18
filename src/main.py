from fastapi import FastAPI
from routes import base, data
from helpers.config import get_settings
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)