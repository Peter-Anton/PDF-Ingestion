from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "PDF Ingestion API"
    APP_VERSION: str = "1.0.0"
    POSTGRES_USER: str = "raguser"
    POSTGRES_PASSWORD: str = "ragpass"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ragdb"
    EMBEDDING_BACKEND: str = "LOCAL"
    EMBEDDING_MODEL_ID: str = "nomic-embed-text"
    EMBEDDING_MODEL_SIZE: int = 384
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 100
    TOP_K: int = 5
    ALLOWED_DIRECTORY: str = "/data"


def get_settings() -> Settings:
    return Settings()
