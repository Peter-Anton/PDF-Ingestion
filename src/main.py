from fastapi import FastAPI
from routes import base, data
from helpers.config import get_settings
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from services.embedding import EmbeddingProviderFactory
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    postgres_conn=f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    app.state.db_engine = create_async_engine(postgres_conn, echo=True)
    app.state.db_client = sessionmaker(app.state.db_engine, expire_on_commit=False, class_=AsyncSession)
    app.state.embedding_client=EmbeddingProviderFactory.create(provider=settings.EMBEDDING_BACKEND)
    app.state.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE)
    try:
        yield
    finally:
        app.state.db_engine.dispose()
        app.state.vector_db_client.disconnect()

app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)