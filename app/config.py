from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from app.utils.logger import logger

# Load standard .env if it exists, which can define APP_ENV
load_dotenv()

ENV = os.getenv("APP_ENV", "development").strip().lower()
logger.info(f"--- ACTIVE ENVIRONMENT: {ENV.upper()} ---")


class Settings(BaseSettings):

    APP_ENV: str = ENV

    MONGO_URI: str = ""
    MONGO_DB: str = ""
    MONGO_COLLECTION: str = ""

    OLLAMA_MODEL: str = ""
    OLLAMA_URL: str = ""
    BATTERY_API_URL: str = ""
    BATTERY_API_TOKEN: str = ""
    VEHICLE_API_URL: str = ""

    # Endpoints loaded dynamically based on environment
    COMBINED_VEHICLE: str = "https://api.girfalco.sa/v2/report/combinedVehicleReport"
    ALERT_ENABLE: str = "https://api.girfalco.sa/v2/alertV2/enable"

    model_config = {
        "env_file": f".env.{ENV}"
    }


settings = Settings()