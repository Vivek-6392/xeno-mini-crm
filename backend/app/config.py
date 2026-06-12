from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/xeno_crm"

    # AI
    GROQ_API_KEY: str = ""

    # Services
    CHANNEL_SERVICE_URL: str = "http://localhost:8001"
    CRM_CALLBACK_URL: str = "http://localhost:8000"

    # App
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
