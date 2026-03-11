from pydantic_settings import BaseSettings
import os


ENV = os.getenv("APP_ENV", "development")


class Settings(BaseSettings):

    APP_ENV: str = ENV

    MONGO_URI: str
    MONGO_DB: str
    MONGO_COLLECTION: str

    OLLAMA_MODEL: str
    OLLAMA_URL: str
    # BATTERY_API_URL: str

    model_config = {
        "env_file": f".env.{ENV}"
    }


settings = Settings()