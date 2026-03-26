import requests
from typing_extensions import Optional
from app.utils.logger import logger
from app.config import settings

BASE_URL = settings.VEHICLE_API_URL
AUTH_TOKEN = settings.BATTERY_API_TOKEN



def get_vehicle_details(imei: str, company_id: Optional[int]=206):

    try:
        if not company_id:
            return {"response": "Company ID is required"}

        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Accept": "*/*",
            "User-Agent": "MyUserAgent"
        }

        # params = {"IMEI": imei}
        params = {"cid": company_id}

        logger.info(f"Calling Vehicle API: {BASE_URL} with cid: {company_id}")

        response = requests.get(
            BASE_URL,
            headers=headers,
            params=params,
            timeout=10
        )

        logger.info(f"Status Code: {response.status_code}")

        # HANDLE HTTP ERRORS EXPLICITLY
        if response.status_code != 200:
            logger.error(f"HTTP Error: {response.status_code}")
            return {
                "response": "Unable to fetch vehicle details"
            }

        data = response.json()

        logger.info(f"API Response: {data}")

        # HANDLE API-LEVEL FAILURE
        if not data.get("success", True):
            logger.error("API returned unsuccessful response")
            return {
                "response": "Vehicle data not available"
            }

        return data

    except requests.exceptions.Timeout:
        logger.exception("Timeout Error")
        return {
            "response": "Request timed out"
        }

    except requests.exceptions.ConnectionError:
        logger.exception("Connection Error")
        return {
            "response": "Unable to connect to vehicle service"
        }

    except requests.exceptions.HTTPError:
        logger.exception("HTTP Error")
        return {
            "response": "Vehicle service error"
        }

    except Exception:
        logger.exception("Unexpected Error")
        return {
            "response": "Some internal error happened"
        }

