import requests

from app.utils.logger import logger
from app.config import settings
from datetime import datetime, timezone, timedelta
from cachetools import cached, TTLCache

api_cache = TTLCache(maxsize=50, ttl=300) # 5 minutes TTL


BASE_URL    = settings.VEHICLE_API_URL
AUTH_TOKEN  = settings.BATTERY_API_TOKEN
COMBINED_URL = settings.COMBINED_VEHICLE


# =========================================================
# FLEET-WIDE COMBINED REPORT  (no vid param)
# =========================================================

import copy

@cached(cache=api_cache)
def _cached_combined_report_fleet(company_id, from_date, to_date):
    try:
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Accept": "*/*",
            "User-Agent": "MyUserAgent"
        }

        params = {
            "cid":      company_id,
            "fromDate": from_date,
            "toDate":   to_date,
            "fullRows": "true"
        }

        logger.info(
            f"[FLEET API] Calling combined report without vid "
            f"| cid={company_id} | {from_date} → {to_date}"
        )

        response = requests.get(
            COMBINED_URL,
            headers=headers,
            params=params,
            timeout=20           # fleet call is heavier than single-vehicle
        )

        logger.info(f"[FLEET API] Status Code: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"[FLEET API] HTTP Error: {response.status_code}")
            return {"success": False, "error": "Unable to fetch fleet data"}

        return response.json()

    except requests.exceptions.Timeout:
        logger.exception("[FLEET API] Timeout")
        return {"success": False, "error": "Fleet API request timed out"}

    except requests.exceptions.ConnectionError:
        logger.exception("[FLEET API] Connection Error")
        return {"success": False, "error": "Unable to connect to fleet service"}

    except Exception:
        logger.exception("[FLEET API] Unexpected Error")
        return {"success": False, "error": "Internal fleet API error"}

def combined_report_fleet(
    company_id: int,
    from_date: str,
    to_date: str
) -> dict:
    return copy.deepcopy(_cached_combined_report_fleet(company_id, from_date, to_date))


# =========================================================
# HELPERS
# =========================================================

def get_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_n_days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y-%m-%d")
