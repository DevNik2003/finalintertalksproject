from pydantic_settings import BaseSettings  # type: ignore
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "RAG Governance API"
    API_V1_STR: str = "/api/v1"
    
    # Security Configuration constraints from requirements
    # Secrets from environment variables
    SECRET_KEY: str = "your-super-secret-key-change-in-production" 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    
    # Document Storage
    DOC_STORAGE_DIR: str = "./uploaded_docs"

    # Qdrant Vector DB (local file storage — no server needed)
    QDRANT_STORAGE_PATH: str = "./qdrant_data"

    model_config = ConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
