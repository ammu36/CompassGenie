import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    Configuration settings for the application.
    """
    # LLM Settings
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")

    # Maps Settings
    MAPS_API_KEY: str = os.environ.get("MAPS_API_KEY", "YOUR_MAPS_API_KEY_HERE")
    MAPS_MOCK_ENABLED: bool = MAPS_API_KEY == "YOUR_MAPS_API_KEY_HERE"

    # LangChain/LLM Model
    LLM_MODEL: str = "gemini-3-flash-preview"
    LLM_TEMPERATURE: float = 1.0
    LLM_THINKING_LEVEL: str = "high"

    # FastAPI Settings
    APP_NAME: str = "CompassGenie Backend API"
    CORS_ORIGINS: list = ["*"]

    class Config:
        case_sensitive = True

settings = Settings()

# Runtime check
if not settings.GEMINI_API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY environment variable not set. LLM calls will fail.")
if settings.MAPS_MOCK_ENABLED:
    print("ℹ️ INFO: MAPS_API_KEY not set. Using mock data for Google Maps.")