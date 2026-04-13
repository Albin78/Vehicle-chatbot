import requests
from typing_extensions import Optional, Any
from app.utils.logger import logger
from app.config import settings


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



def get_operation_summary(
    id: int,
    company_id: int,
    from_date: str,
    to_date: str
):
    try:
        if not id:
            return {"response": "ID is required"}

        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Accept": "*/*",
            "User-Agent": "MyUserAgent"
        }

        url = "https://api.girfalco.sa/v2/report/operationSummary"

        params = {
            "vehicleID": id,
            "fromDate": from_date,
            "toDate": to_date,
            "vehicleType": "All",
            "vehicleGroup": "All",
            "cid": company_id,
            "vgid": "",
            "type": "daily",
            "page": 1,
            "row": 10
        }

        logger.info(f"Calling Operation Summary API for vehicleID: {id}")

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        logger.info(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"HTTP Error: {response.status_code}")
            return {"response": "Unable to fetch operation summary"}

        data = response.json()

        if not data.get("dataRows"):
            return {"response": "No data available for this vehicle"}

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