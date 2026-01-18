"""Application configuration - Production ready settings"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "RAG Education System"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database - Use environment variable directly
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL", 
        "postgresql://rag_user:rag_secure_pwd_2026@localhost:5432/rag_education"
    )
    
    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    
    # Gemini
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    
    # Storage
    UPLOAD_DIR: str = "./uploads"
    CHROMA_DIR: str = "./storage/chroma_db"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_FILES_PER_UPLOAD: int = 10
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # CORS - Set CORS_ORIGINS env var as comma-separated list for production
    CORS_ORIGINS_STR: str = os.environ.get(
        "CORS_ORIGINS_STR",
        "http://localhost:5173,http://localhost:3000"
    )
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()
