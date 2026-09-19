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
    TOP_K: int
    ALLOWED_DIRECTORY: str 
    EMBEDDING_CONCURRENCY: int = 2
    HYBRID_RRF_K: int = 60
    MIN_RELEVANCE_SCORE: float = 0.55


def get_settings() -> Settings:
    return Settings()
