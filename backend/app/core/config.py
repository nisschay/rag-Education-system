"""Application configuration - Production ready settings"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "RAG Education System"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql://rag_user:rag_secure_pwd_2026@localhost:5432/rag_education"
    
    # Security
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # Gemini
    GEMINI_API_KEY: str = ""
    
    # Storage
    UPLOAD_DIR: str = "./uploads"
    CHROMA_DIR: str = "./storage/chroma_db"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_FILES_PER_UPLOAD: int = 10
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # CORS - Add your production domains here
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
