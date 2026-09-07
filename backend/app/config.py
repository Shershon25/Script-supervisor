import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load root .env file if it exists
root_env = Path(__file__).resolve().parent.parent.parent / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env)

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://root@localhost:26257/script_supervisor?sslmode=disable"
    
    # Gemini Mode: 'vertexai' or 'developer'
    GEMINI_PROVIDER: str = "developer"
    
    # Google Cloud Vertex AI settings (Uses Application Default Credentials / ADC)
    GCP_PROJECT_ID: str = ""
    GCP_LOCATION: str = "global"
    
    # Gemini Developer API settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Parallel API settings (External Research)
    PARALLEL_API_KEY: str = ""
    
    # Document Import Limits
    MAX_IMPORT_FILE_SIZE_MB: int = 15
    MAX_IMPORTED_SCENES: int = 200
    MAX_EXTRACTED_TEXT_SIZE: int = 2000000
    MAX_DOCUMENT_CHARACTERS: int = 2000000

    # Environment & Transport Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:3000"
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Per-Minute IP Rate Limits (Requests per minute per IP)
    RATE_LIMIT_CHEAP_PER_MIN: int = 120
    RATE_LIMIT_WRITE_PER_MIN: int = 30
    RATE_LIMIT_ANALYSIS_PER_MIN: int = 10
    RATE_LIMIT_RESEARCH_PER_MIN: int = 5
    RATE_LIMIT_IMPORT_PER_MIN: int = 3

    # Daily IP Usage Protection Caps (Maximum executions per IP per 24 hours)
    MAX_ANALYSES_PER_IP_PER_DAY: int = 50
    MAX_RESEARCH_REQUESTS_PER_IP_PER_DAY: int = 20
    MAX_IMPORTS_PER_IP_PER_DAY: int = 10

    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = "agentic_cinema_secret_key_2026_super_secure_jwt_token_key"
    JWT_ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    
    model_config = SettingsConfigDict(
        env_file=str(root_env) if root_env.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
