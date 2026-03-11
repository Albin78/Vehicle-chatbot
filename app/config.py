from pydantic import BaseSettings


class Settings(BaseSettings):

    APP_ENV: str = "dev"

    MONGO_URI: str
    MONGO_DB: str

    OLLAMA_MODEL: str
    OLLAMA_URL: str = "http://localhost:11434"

    BATTERY_API_URL: str

    class Config:
        env_file = ".env"


settings = Settings()