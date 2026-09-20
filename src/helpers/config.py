from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str 
    APP_VERSION: str 
    POSTGRES_USER: str 
    POSTGRES_PASSWORD: str 
    POSTGRES_HOST: str 
    POSTGRES_PORT: int 
    POSTGRES_DATABASE: str 
    EMBEDDING_BACKEND: str 
    EMBEDDING_MODEL_ID: str 
    EMBEDDING_MODEL_SIZE: int 
    CHUNK_SIZE: int 
    CHUNK_OVERLAP: int 
    INGESTION_WORKERS: int = 1
    INGESTION_QUEUE_SIZE: int = 100
    TOP_K: int
    ALLOWED_DIRECTORY: str 
    HYBRID_RRF_K: int 
    MIN_RELEVANCE_SCORE: float 


def get_settings() -> Settings:
    return Settings()
