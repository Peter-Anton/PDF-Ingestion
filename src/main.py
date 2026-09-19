from fastapi import FastAPI
from time import perf_counter
import logging
from routes import base, ingest, search
from helpers.config import get_settings
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from services.embedding.EmbeddingProviderFactory import EmbeddingProviderFactory

logger = logging.getLogger("uvicorn.error")


async def request_metrics(request, call_next):
    started_at = perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        elapsed_ms = (perf_counter() - started_at) * 1000
        status_code = response.status_code if response is not None else 500
        logger.info(
            "request method=%s path=%s status=%s latency_ms=%.2f",
            request.method,
            request.url.path,
            status_code,
            elapsed_ms,
        )


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
app.middleware("http")(request_metrics)

app.include_router(base.base_router)
app.include_router(ingest.ingest_router)
app.include_router(search.search_router)
app.include_router(ingest.ingest_router, prefix="/api/v1")
app.include_router(search.search_router, prefix="/api/v1")