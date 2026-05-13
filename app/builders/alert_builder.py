from collections import Counter
from datetime import datetime
import re


# =========================================================
# HELPERS
# =========================================================

def parse_alert_date(date_str: str):

    return datetime.fromisoformat(
        date_str.replace("Z", "+00:00")
    )


def convert_duration_to_seconds(duration: str | None) -> int:

    """
    Converts:
        '1hr 31mins 7secs'
    into:
        5467 seconds
    """

    if not duration:
        return 0

    hours = 0
    minutes = 0
    seconds = 0

    hr_match = re.search(r"(\d+)\s*hr", duration)
    min_match = re.search(r"(\d+)\s*min", duration)
    sec_match = re.search(r"(\d+)\s*sec", duration)

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


# =========================================================
# ALERT ANALYZERS
# =========================================================

def analyze_overspeed(alert, analytics):

    """
    Tracks:
    - highest overspeed event
    - overspeed count
    """

    analytics["overspeed_count"] += 1

    value = alert.get("OrginalValue")

    if value is None:
        return

    if value > analytics["highest_overspeed_value"]:

        analytics["highest_overspeed_value"] = value

        analytics["highest_overspeed"] = {
            "speed": alert.get("CurrentValue"),
            "original_speed": value,
            "limit": alert.get("Limit"),
            "time": alert.get("Date"),
            "duration": alert.get("Duration"),
            "location": alert.get("Location")
        }


def analyze_idling(alert, analytics):

    """
    Tracks:
    - longest idling event
    - idling count
    """

    analytics["idling_count"] += 1

    duration_text = alert.get("Duration")

    duration_seconds = convert_duration_to_seconds(
        duration_text
    )

    if duration_seconds > analytics["longest_idle_seconds"]:

        analytics["longest_idle_seconds"] = duration_seconds

        analytics["longest_idle"] = {
            "duration": duration_text,
            "duration_seconds": duration_seconds,
            "limit": alert.get("Limit"),
            "time": alert.get("Date"),
            "location": alert.get("Location")
        }


def analyze_afterhours(alert, analytics):

    analytics["afterhours_count"] += 1


# =========================================================
# MAIN ALERT BUILDER
# =========================================================

def build_alert_response(intent, api_result):

    alerts = api_result.get("results", [])

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
        key=lambda x: parse_alert_date(x["Date"]),
        reverse=True
    )

    latest_alert = alerts_sorted[0]

    # =====================================================
    # ANALYTICS STORAGE
    # =====================================================

    analytics = {

        # counts
        "overspeed_count": 0,
        "idling_count": 0,
        "afterhours_count": 0,

        # overspeed
        "highest_overspeed_value": 0,
        "highest_overspeed": None,

        # idling
        "longest_idle_seconds": 0,
        "longest_idle": None
    }

    # =====================================================
    # ALERT DISTRIBUTION
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

        if alert_name == "Overspeed":

            analyze_overspeed(
                alert,
                analytics
            )

        # -------------------------------------------------
        # IDLING
        # -------------------------------------------------

        elif alert_name == "Idling":

            analyze_idling(
                alert,
                analytics
            )

        # -------------------------------------------------
        # AFTER HOURS
        # -------------------------------------------------

        elif alert_name == "Afterhoursmovement":

            analyze_afterhours(
                alert,
                analytics
            )

    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {

        "type": "alert_summary",

        "total_alerts": len(alerts),

        "alert_distribution":
            dict(alert_distribution),

        # -------------------------------------------------
        # latest alert
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
                latest_alert.get("Duration")
        },

        # -------------------------------------------------
        # overspeed analytics
        # -------------------------------------------------

        "overspeed": {

            "count":
                analytics["overspeed_count"],

            "highest":
                analytics["highest_overspeed"]
        },

        # -------------------------------------------------
        # idling analytics
        # -------------------------------------------------

        "idling": {

            "count":
                analytics["idling_count"],

            "longest":
                analytics["longest_idle"]
        },

        # -------------------------------------------------
        # afterhours
        # -------------------------------------------------

        "afterhoursmovement": {

            "count":
                analytics["afterhours_count"]
        }
    }