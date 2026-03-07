from pydantic_settings import BaseSettings

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
    BUILD_VERSION: str = "dev"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

settings = Settings()
