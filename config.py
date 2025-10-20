"""Configuration management for the application."""
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # Anthropic API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # BLS API
    BLS_API_KEY: Optional[str] = os.getenv("BLS_API_KEY", "")
    BLS_API_BASE_URL: str = os.getenv(
        "BLS_API_BASE_URL",
        "https://api.bls.gov/publicAPI/v2"
    )
    BLS_API_TIMEOUT: int = 30
    
    # Application
    APP_TITLE: str = os.getenv("APP_TITLE", "BLS Data Intelligence Assistant")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    MAX_SERIES_PER_REQUEST: int = int(os.getenv("MAX_SERIES_PER_REQUEST", "25"))
    
    # Semantic Kernel
    SK_MAX_TOKENS: int = 4000
    SK_TEMPERATURE: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def validate(self) -> bool:
        """Validate required settings."""
        if not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required")
        return True


settings = Settings()

# Validate on import
try:
    settings.validate()
except ValueError as e:
    print(f"Configuration error: {e}")
    print("Please check your .env file and ensure all required API keys are set.")