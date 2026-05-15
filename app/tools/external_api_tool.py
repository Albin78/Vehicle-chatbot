import requests
from typing_extensions import Optional, Any
from app.utils.logger import logger
from app.config import settings
from datetime import datetime


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



def combined_report(
    vehicle_id: int | None,
    company_id: int | None,
    from_date: datetime | None,
    to_date: datetime | None
):
    try:
        if not vehicle_id:
            return {"response": "ID is required"}

        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Accept": "*/*",
            "User-Agent": "MyUserAgent"
        }

        url = "https://api.girfalco.sa/v2/report/combinedVehicleReport"

        params = {
            "vid": vehicle_id,
            "fromDate": from_date,
            "toDate": to_date,
            "cid": company_id,
            "fullRows": "true"
        }

        logger.info(f"Calling Combined Report API for vehicleID: {vehicle_id}")

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

        # if not data.get("dataRows"):
        #     return {"response": "No data available for this vehicle"}

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
    
