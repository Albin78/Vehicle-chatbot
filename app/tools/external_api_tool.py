import requests
from typing_extensions import Optional
from app.utils.logger import logger
from app.config import settings

BASE_URL = settings.VEHICLE_API_URL
AUTH_TOKEN = settings.BATTERY_API_TOKEN



def get_vehicle_details(imei: Optional[str]=None, company_id: Optional[int]=16):

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
        vehicle_count = data.get("VehicleCount", [])

        logger.info(f"API Response: {data}")
        logger.info(f"Total Vehicle Count: {vehicle_count[0].get('TotalCount', 0)}")

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



def get_vehicle_by_imei(api_response: dict, imei: Optional[str]):
    vehicle_list = api_response.get("VehicleList", [])
    logger.info(f"Vehicle list fetched: {vehicle_list}")
    
    # Build map (can cache this)
    vehicle_map = {v["IMEI"]: v for v in vehicle_list}
    logger.info(f"Vehicle Map: {vehicle_map}")
    
    return vehicle_map.get(imei)