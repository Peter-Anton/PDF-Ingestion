from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    APP_NAME : str
    APP_VERSION : str
    FILE_ALLOWED_EXTENSIONS: list
    FILE_MAX_SIZE_MB: int
    FILE_MAX_CHUNK_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DATABASE: str
    GENERATION_BACKEND : str
    EMBEDDING_BACKEND : str
    GENERATION_MODEL_ID : str
    EMBEDDING_MODEL_ID : str
    EMBEDDING_MODEL_SIZE : int
    INPUT_DEFAULT_MAX_CHARACTERS : int
    GENERATION_DEFAULT_MAX_TOKENS : int
    GENERATION_DEFAULT_TEMPERATURE : float
    VECTOR_DB_BACKEND:str
    VECTOR_DB_PATH:str
    VECTOR_DB_DISTANCE_METRIC:str
    DEAFULT_LANGUAGE:str
    PRIMARY_LANGUAGE:str



    class Config:
        env_file= ".env"
def get_settings():
    return Settings()       
