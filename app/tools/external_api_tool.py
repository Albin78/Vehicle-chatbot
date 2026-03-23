import requests
from app.utils.logger import logger
from app.config import settings

BASE_URL = settings.BATTERY_API_URL
AUTH_TOKEN = settings.BATTERY_API_TOKEN


# def get_vehicle_details(imei: str):

#     try:
#         if not imei:
#             return {"error": "IMEI is required"}
        
#         # internal_api_url = f"{INTERNAL_API_BASE}?IMEI={imei}"
#         # headers = {
#         #     "Authorization": f"Bearer {AUTH_TOKEN}",
#         #     "Accept": "application/json",
#         # }

#         url = f"{BASE_URL}?IMEI={imei}"
#         headers = {
#             "Authorization": f"Bearer {AUTH_TOKEN}",
#             "Accept": "*/*",
#             "User-Agent": "PostmanRuntime/7.37.3"
#         }
#         print("Headers: ",headers)
#         # logger.info(f"Headers: {headers}")
#         logger.info(f"Calling Vehicle API: {url}")

#         response = requests.get(url, timeout=10, headers=headers)
#         response.raise_for_status()
        
#         logger.info(f"Vehicle API response: {response}")

#         # if response.status_code != 200:
#         if not response:
#             logger.error(f"Vehicle API failed: {response.status_code}")
#             return {"error": "Vehicle API request failed"}

#         data = response.json()

#         return data

#     except Exception as e:
#         logger.exception("Vehicle API Exception")
#         return {"error": str(e)}




def get_vehicle_details(imei: str):

    try:
        if not imei:
            return {"error": "IMEI is required"}

        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Accept": "*/*",
            "User-Agent": "PostmanRuntime/7.37.3"
        }

        params = {"IMEI": imei}

        logger.info(f"Calling Vehicle API: {BASE_URL} with IMEI: {imei}")

        response = requests.get(
            BASE_URL,
            headers=headers,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response: {response.text}")

        data = response.json()
        logger.info(f" Type of Data: {type(data)}")
        logger.info(f" Vehicle Data: {data}")
        return data

    except Exception as e:
        logger.exception("Vehicle API Exception")
        return {"error": str(e)}

