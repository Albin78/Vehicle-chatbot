import requests

from app.utils.logger import logger
from app.config import settings
from datetime import datetime, timezone, timedelta


BASE_URL    = settings.VEHICLE_API_URL
AUTH_TOKEN  = settings.BATTERY_API_TOKEN
COMBINED_URL = settings.COMBINED_VEHICLE


# =========================================================
# FLEET-WIDE COMBINED REPORT  (no vid param)
# =========================================================

def combined_report_fleet(
    company_id: int,
    from_date: str,
    to_date: str
) -> dict:
    """
    Fetches the combined report for ALL vehicles in the fleet.

    This is identical to combined_report() in external_api_tool.py
    but intentionally omits the 'vid' parameter so the API returns
    lastRecords, alerts, and operationSummary for every vehicle
    belonging to the company in a single call.

    Args:
        company_id: Company identifier.
        from_date:  Start date string  "YYYY-MM-DD".
        to_date:    End date string    "YYYY-MM-DD".

    Returns:
        Raw API dict with keys:
          - success
          - lastRecords.data[]          (per-vehicle live snapshot)
          - lastRecords.overAllCount    (pre-aggregated fleet counts)
          - alerts.results[]            (alert events in date range)
          - operationSummary.dataRows[] (per-vehicle-per-day rows)
          - operationSummary.summary    (fleet-level totals)
    """
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


# =========================================================
# HELPERS
# =========================================================

def get_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_n_days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y-%m-%d")
