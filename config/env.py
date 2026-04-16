    # Individual DB fields (PostgreSQL preferred)
from pydantic_settings import BaseSettings,SettingsConfigDict
from typing import Optional, List
import sys
from functools import lru_cache


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: Optional[str] = None
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    
    
 
    # =============================================================================
    # EMAIL
    # =============================================================================

    # Email Configuration
    EMAIL_BACKEND: str = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USE_TLS: bool = True
    EMAIL_HOST_USER: str
    EMAIL_HOST_PASSWORD: str
    SITE_BASE_URL: str = "http://localhost:8000"   
    

    
@lru_cache
def get_settings() -> EnvSettings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    This improves performance and ensures consistency.

    Returns:
        EnvSettings: Validated settings instance

    Raises:
        SystemExit: If validation fails (with helpful error message)
    """
    try:
        # Pylance may complain about missing required fields (like SECRET_KEY)
        # but Pydantic Settings will load them from the environment/.env at runtime.
        return EnvSettings()  # type: ignore
    except Exception as e:
        # Beautiful error handling for Juniors
        sys.stderr.write(f"\n❌ Environment validation failed:\n{e}\n")
        sys.stderr.write(
            "\nMake sure you have a .env file with all required variables.\n"
        )
        sys.stderr.write("See .env.example for reference.\n\n")
        sys.exit(1)


# Global settings instance - import this in other modules
# Usage: from config.env import env
env = get_settings()
