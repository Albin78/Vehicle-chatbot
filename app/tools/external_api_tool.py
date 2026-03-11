import requests
from app.config import settings


def battery_service(imei):

    response = requests.get(
        f"{settings.BATTERY_API_URL}/{imei}"
    )

    return response.json()