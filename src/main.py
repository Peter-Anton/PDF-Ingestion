from fastapi import FastAPI
from routes import base, data
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from contextlib import asynccontextmanager
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from routes.nlp import nlp_router
from stores.llm.templates.template_parser import TemplateParser
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # Attach clients to app.state
    app.state.mongo_conn = AsyncIOMotorClient(settings.MONGO_URL)
    app.state.db_client = app.state.mongo_conn[settings.MONGO_DATABASE]
    llm_provider_factory=LLMProviderFactory(settings)
    vector_db_provider_factory=VectorDBProviderFactory(settings)
    app.state.generation_client=llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.state.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)
    app.state.embedding_client=llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.state.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE)
    app.state.vector_db_client=vector_db_provider_factory.create(provider=settings.VECTOR_DB_BACKEND) 
    app.state.template_parser=TemplateParser(language=settings.PRIMARY_LANGUAGE,default_language=settings.DEAFULT_LANGUAGE)
    app.state.vector_db_client.connect()
    try:
        yield
    finally:
        app.state.mongo_conn.close()
        app.state.vector_db_client.disconnect()

# Pass the lifespan handler to FastAPI
app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp_router)