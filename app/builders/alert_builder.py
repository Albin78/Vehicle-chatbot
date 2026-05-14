from collections import Counter
from datetime import datetime
import re


# =========================================================
# HELPERS
# =========================================================

def parse_alert_date(date_str: str):

    if not date_str:
        return datetime.min

    try:
        return datetime.fromisoformat(
            date_str.replace("Z", "+00:00")
        )

    except Exception:
        return datetime.min


def convert_duration_to_seconds(
    duration: str | None
) -> int:

    """
    Converts:
        '1hr 31mins 7secs'
    into:
        5467
    """

    if not duration:
        return 0

    hours = 0
    minutes = 0
    seconds = 0

    hr_match = re.search(
        r"(\d+)\s*hr",
        duration,
        re.IGNORECASE
    )

    min_match = re.search(
        r"(\d+)\s*min",
        duration,
        re.IGNORECASE
    )

    sec_match = re.search(
        r"(\d+)\s*sec",
        duration,
        re.IGNORECASE
    )

    if hr_match:
        hours = int(hr_match.group(1))

    if min_match:
        minutes = int(min_match.group(1))

    if sec_match:
        seconds = int(sec_match.group(1))

    return (
        hours * 3600
        + minutes * 60
        + seconds
    )


def safe_float(value):

    try:
        return float(value)

    except Exception:
        return 0.0


# =========================================================
# ALERT ANALYZERS
# =========================================================

def analyze_overspeed(alert, analytics):

    analytics["overspeed"]["count"] += 1

    value = safe_float(
        alert.get("OrginalValue")
    )

    if value > analytics["overspeed"]["highest_value"]:

        analytics["overspeed"]["highest_value"] = value

        analytics["overspeed"]["highest"] = {

            "speed":
                alert.get("CurrentValue"),

            "original_speed":
                value,

            "limit":
                alert.get("Limit"),

            "time":
                alert.get("Date"),

            "duration":
                alert.get("Duration"),

            "location":
                alert.get("Location")
        }


def analyze_idling(alert, analytics):

    analytics["idling"]["count"] += 1

    duration_text = alert.get("Duration")

    duration_seconds = convert_duration_to_seconds(
        duration_text
    )

    if duration_seconds > analytics["idling"]["longest_seconds"]:

        analytics["idling"]["longest_seconds"] = duration_seconds

        analytics["idling"]["longest"] = {

            "duration":
                duration_text,

            "duration_seconds":
                duration_seconds,

            "limit":
                alert.get("Limit"),

            "time":
                alert.get("Date"),

            "location":
                alert.get("Location")
        }


def analyze_afterhours(alert, analytics):

    analytics["afterhoursmovement"]["count"] += 1


# =========================================================
# MAIN BUILDER
# =========================================================

def build_alert_response(intent, api_result):

    alerts_section = api_result.get("alerts")

    if not isinstance(alerts_section, dict):

        return {
            "type": "error",
            "message": "Alert data unavailable."
        }

    alerts = alerts_section.get("results", [])

    if not alerts:

        return {
            "type": "error",
            "message": (
                "No alerts found for the selected "
                "time range."
            )
        }

    # =====================================================
    # SORT ALERTS
    # =====================================================

    alerts_sorted = sorted(

        alerts,

        key=lambda x: parse_alert_date(
            x.get("Date")
        ),

        reverse=True
    )

    latest_alert = alerts_sorted[0]

    # =====================================================
    # ANALYTICS STORAGE
    # =====================================================

    analytics = {

        "overspeed": {

            "count": 0,

            "highest_value": 0,

            "highest": None
        },

        "idling": {

            "count": 0,

            "longest_seconds": 0,

            "longest": None
        },

        "afterhoursmovement": {

            "count": 0
        }
    }

    # =====================================================
    # DISTRIBUTION
    # =====================================================

    alert_distribution = Counter()

    # =====================================================
    # MAIN LOOP
    # =====================================================

    for alert in alerts:

        alert_name = alert.get("AlertName")

        if not alert_name:
            continue

        alert_distribution[alert_name] += 1

        # -------------------------------------------------
        # OVERSPEED
        # -------------------------------------------------

        if alert_name.lower() == "overspeed":

            analyze_overspeed(
                alert,
                analytics
            )

        # -------------------------------------------------
        # IDLING
        # -------------------------------------------------

        elif alert_name.lower() == "idling":

            analyze_idling(
                alert,
                analytics
            )

        # -------------------------------------------------
        # AFTER HOURS
        # -------------------------------------------------

        elif alert_name.lower() == "afterhoursmovement":

            analyze_afterhours(
                alert,
                analytics
            )

    # =====================================================
    # MOST COMMON ALERT
    # =====================================================

    most_common_alert = None

    if alert_distribution:

        most_common_alert = max(
            alert_distribution.items(),
            key=lambda x: x[1]
        )[0]

    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {

        "type": "alert_summary",

        "vehicle":
            intent.vehicle_id,

        "total_alerts":
            len(alerts),

        "alert_distribution":
            dict(alert_distribution),

        "most_common_alert":
            most_common_alert,

        # -------------------------------------------------
        # LATEST ALERT
        # -------------------------------------------------

        "latest_alert": {

            "alert_name":
                latest_alert.get("AlertName"),

            "time":
                latest_alert.get("Date"),

            "limit":
                latest_alert.get("Limit"),

            "value":
                latest_alert.get("CurrentValue"),

            "duration":
                latest_alert.get("Duration"),

            "location":
                latest_alert.get("Location")
        },

        # -------------------------------------------------
        # OVERSPEED
        # -------------------------------------------------

        "overspeed":
            analytics["overspeed"],

        # -------------------------------------------------
        # IDLING
        # -------------------------------------------------

        "idling":
            analytics["idling"],

        # -------------------------------------------------
        # AFTER HOURS
        # -------------------------------------------------

        "afterhoursmovement":
            analytics["afterhoursmovement"]
    }