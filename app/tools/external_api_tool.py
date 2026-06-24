import requests
from typing import Optional
from app.utils.logger import logger
from app.config import settings
from datetime import datetime
from cachetools import cached, TTLCache

api_cache = TTLCache(maxsize=100, ttl=300) # 5 minutes TTL


BASE_URL = settings.VEHICLE_API_URL
AUTH_TOKEN = settings.BATTERY_API_TOKEN



def get_vehicle_details(company_id: Optional[int]=16):

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

        # logger.info(f"API Response: {data}")
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



import copy

@cached(cache=api_cache)
def _cached_combined_report(vehicle_id, company_id, from_date, to_date):
    try:
        if not vehicle_id:
            return {"response": "ID is required"}

        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Accept": "*/*",
            "User-Agent": "MyUserAgent"
        }

        url = settings.COMBINED_VEHICLE

        params = {
            "vid": vehicle_id,
            "fromDate": from_date,
            "toDate": to_date,
            "cid": company_id,
            "fullRows": "true"
        }

        logger.info(f"Calling Combined Report API: {url} for vehicleID: {vehicle_id}")

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        ) 
        logger.info(f"Response from combined report API: {response}")

        logger.info(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"HTTP Error: {response.status_code}")
            return {"response": "Unable to fetch operation summary"}

        data = response.json()

        return data

    except requests.exceptions.Timeout:
        logger.exception("Timeout Error")
        return {"response": "Request timed out"}

    except requests.exceptions.ConnectionError:
        logger.exception("Connection Error")
        return {"response": "Unable to connect to report service"}

    except Exception:
        logger.exception("Unexpected Error")
        return {"response": "Some internal error happened"}

def combined_report(
    vehicle_id: int | None,
    company_id: int | None,
    from_date: datetime | None,
    to_date: datetime | None
):
    return copy.deepcopy(_cached_combined_report(vehicle_id, company_id, from_date, to_date))
    


# =========================================================
# ALERT ENABLE STATUS API
# =========================================================

@cached(cache=api_cache)
def get_alert_enable_status(
    company_id: int,
    vehicle_id: int | None = None,
    row: int = 100,
    page: int = 1
):
    try:
        if not company_id:
            return {"response": "Company ID is required"}

        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Accept": "*/*",
            "User-Agent": "MyUserAgent"
        }

        url = settings.ALERT_ENABLE

        params = {
            "cid": company_id,
            "row": row,
            "page": page,
            "vgid": "",
            "TypeID": 1
        }

        logger.info(
            f"Calling Alert Enable Status API: {url} with cid={company_id}"
        )

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        logger.info(f"Alert Enable API status code: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"HTTP Error: {response.status_code}")
            return {"response": "Unable to fetch alert enable status"}

        data = response.json()
        return data

    except requests.exceptions.Timeout:
        logger.exception("Timeout Error")
        return {"response": "Request timed out"}

    except requests.exceptions.ConnectionError:
        logger.exception("Connection Error")
        return {"response": "Unable to connect to alert enable service"}

    except Exception:
        logger.exception("Unexpected Error")
        return {"response": "Some internal error happened"}

    
