from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    anam_api_key: str
    
    # Anam AI Configuration
    anam_api_base_url: str = "https://api.anam.ai"
    anam_avatar_id: str = "d9ebe82e-2f34-4ff6-9632-16cb73e7de08"  # Default
    anam_voice_id: str = "6bfbe25a-979d-40f3-a92b-5394170af54b"   # Default

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore environment variables not listed here

# Global settings instance
settings = Settings()

# Shared constants for ChromaDB and embeddings
CHROMA_PATH = "chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
