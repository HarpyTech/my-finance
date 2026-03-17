from pydantic_settings import BaseSettings
import logging

# Configure logging before any other code runs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Secure FastAPI"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    DEFAULT_LOGIN_PASSWORD: str

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "my_finance"
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    BUILD_VERSION: str = "dev"

    model_config = {"env_file": ".env", "case_sensitive": True}


try:
    settings = Settings()
    logger.info("Configuration loaded successfully")
    logger.info(f"Project: {settings.PROJECT_NAME}")
    logger.info(f"MongoDB Database: {settings.MONGODB_DB}")
    logger.info(f"Build Version: {settings.BUILD_VERSION}")
except Exception as exc:
    logger.error(f"Failed to load configuration: {str(exc)}", exc_info=True)
    raise
