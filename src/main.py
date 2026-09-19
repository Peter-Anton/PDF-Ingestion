from fastapi import FastAPI
from routes import base, ingest, search
from helpers.config import get_settings
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from services.embedding.EmbeddingProviderFactory import EmbeddingProviderFactory
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    postgres_conn=f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DATABASE}"
    app.state.db_engine = create_async_engine(postgres_conn, echo=True)
    app.state.db_client = sessionmaker(app.state.db_engine, expire_on_commit=False, class_=AsyncSession)
    app.state.embedding_client=EmbeddingProviderFactory.create(provider=settings.EMBEDDING_BACKEND)
    app.state.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE)
    try:
        yield
    finally:
        await app.state.db_engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(ingest.ingest_router)
app.include_router(search.search_router)
app.include_router(ingest.ingest_router, prefix="/api/v1")
app.include_router(search.search_router, prefix="/api/v1")