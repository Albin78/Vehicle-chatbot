from collections import Counter, defaultdict
from app.parsers.builder_parsers import (
    parse_alert_date,
    extract_date_only,
    convert_duration_to_seconds,
    safe_float
)


# =========================================================
# ANALYZERS
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
# SHARED PREPROCESSING
# =========================================================

def preprocess_alerts(alerts):

    alerts_sorted = sorted(

        alerts,

        key=lambda x: parse_alert_date(
            x.get("Date")
        ),

        reverse=True
    )

    latest_alert = alerts_sorted[0]

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

    alert_distribution = Counter()

    daily_alerts = defaultdict(int)

    # =====================================================
    # LOOP
    # =====================================================

    for alert in alerts:

        alert_name = alert.get("AlertName")

        if not alert_name:
            continue

        alert_distribution[alert_name] += 1

        alert_date = extract_date_only(
            alert.get("Date")
        )

        daily_alerts[alert_date] += 1

        normalized_name = alert_name.lower()

        if normalized_name == "overspeed":

            analyze_overspeed(
                alert,
                analytics
            )

        elif normalized_name == "idling":

            analyze_idling(
                alert,
                analytics
            )

        elif normalized_name == "afterhoursmovement":

            analyze_afterhours(
                alert,
                analytics
            )

    peak_alert_day = None

    if daily_alerts:

        peak_alert_day = max(
            daily_alerts.items(),
            key=lambda x: x[1]
        )[0]

    most_common_alert = None

    if alert_distribution:

        most_common_alert = max(
            alert_distribution.items(),
            key=lambda x: x[1]
        )[0]

    return {

        "alerts_sorted":
            alerts_sorted,

        "latest_alert":
            latest_alert,

        "analytics":
            analytics,

        "alert_distribution":
            dict(alert_distribution),

        "daily_alerts":
            dict(daily_alerts),

        "peak_alert_day":
            peak_alert_day,

        "most_common_alert":
            most_common_alert
    }



def build_overspeed_summary_response(
    intent,
    processed
):

    return {

        "type":
            "overspeed_summary",

        "vehicle":
            intent.vehicle_id,

        "overspeed":
            processed["analytics"]["overspeed"],

        "daily_alerts":
            processed["daily_alerts"],

        "latest_alert":
            processed["latest_alert"]
    }



def build_idling_summary_response(
    intent,
    processed
):

    return {

        "type":
            "idling_summary",

        "vehicle":
            intent.vehicle_id,

        "idling":
            processed["analytics"]["idling"],

        "daily_alerts":
            processed["daily_alerts"],

        "latest_alert":
            processed["latest_alert"]
    }



def build_afterhours_summary_response(
    intent,
    processed
):

    return {

        "type":
            "afterhours_summary",

        "vehicle":
            intent.vehicle_id,

        "afterhoursmovement":
            processed["analytics"]["afterhoursmovement"],

        "daily_alerts":
            processed["daily_alerts"],

        "latest_alert":
            processed["latest_alert"]
    }


# =========================================================
# ALERT COUNT RESPONSE
# =========================================================

def build_alert_count_response(
    intent,
    alerts,
    processed
):

    return {

        "type":
            "alert_count",

        "vehicle":
            intent.vehicle_id,

        "total_alerts":
            len(alerts)
    }


# =========================================================
# LATEST ALERT RESPONSE
# =========================================================

def build_latest_alert_response(
    intent,
    processed
):

    latest = processed["latest_alert"]

    return {

        "type":
            "latest_alert",

        "vehicle":
            intent.vehicle_id,

        "latest_alert": {

            "alert_name":
                latest.get("AlertName"),

            "time":
                latest.get("Date"),

            "limit":
                latest.get("Limit"),

            "value":
                latest.get("CurrentValue"),

            "duration":
                latest.get("Duration"),

            "location":
                latest.get("Location")
        }
    }


# =========================================================
# DAILY ALERT SUMMARY
# =========================================================

def build_daily_alert_summary_response(
    intent,
    processed
):

    return {

        "type":
            "daily_alert_summary",

        "vehicle":
            intent.vehicle_id,

        "daily_alerts":
            processed["daily_alerts"],

        "peak_alert_day":
            processed["peak_alert_day"]
    }


# =========================================================
# FULL SUMMARY
# =========================================================

def build_full_alert_summary_response(
    intent,
    alerts,
    processed
):

    latest = processed["latest_alert"]

    return {

        "type":
            "alert_summary",

        "vehicle":
            intent.vehicle_id,

        "total_alerts":
            len(alerts),

        "alert_distribution":
            processed["alert_distribution"],

        "most_common_alert":
            processed["most_common_alert"],

        "daily_alerts":
            processed["daily_alerts"],

        "peak_alert_day":
            processed["peak_alert_day"],

        "latest_alert": {

            "alert_name":
                latest.get("AlertName"),

            "time":
                latest.get("Date"),

            "limit":
                latest.get("Limit"),

            "value":
                latest.get("CurrentValue"),

            "duration":
                latest.get("Duration"),

            "location":
                latest.get("Location")
        },

        "overspeed":
            processed["analytics"]["overspeed"],

        "idling":
            processed["analytics"]["idling"],

        "afterhoursmovement":
            processed["analytics"]["afterhoursmovement"]
    }


# =========================================================
# MAIN ROUTER
# =========================================================

def build_alert_response(intent, api_result):

    alerts_section = api_result.get("alerts")

    if not isinstance(alerts_section, dict):

        return {

            "type": "error",

            "message":
                "Alert data unavailable."
        }

    alerts = alerts_section.get("results", [])

    if not alerts:

        return {

            "type": "error",

            "message":
                "No alerts found for the selected time range."
        }

    processed = preprocess_alerts(alerts)

    response_type = intent.alert_response_type

    # =====================================================
    # ALERT COUNT
    # =====================================================

    if response_type == "alert_count":

        return build_alert_count_response(
            intent,
            alerts,
            processed
        )

    # =====================================================
    # LATEST ALERT
    # =====================================================

    elif response_type == "latest_alert":

        return build_latest_alert_response(
            intent,
            processed
        )

    # =====================================================
    # DAILY ALERT SUMMARY
    # =====================================================

    elif response_type == "daily_alert_summary":

        return build_daily_alert_summary_response(
            intent,
            processed
        )
    
    # =====================================================
    # OVERSPEED SUMMARY
    # =====================================================

    elif response_type == "overspeed_summary":

        return build_overspeed_summary_response(
            intent,
            processed
        )

    # =====================================================
    # IDLING SUMMARY
    # =====================================================

    elif response_type == "idling_summary":

        return build_idling_summary_response(
            intent,
            processed
        )

    # =====================================================
    # AFTER HOURS SUMMARY
    # =====================================================

    elif response_type == "afterhours_summary":

        return build_afterhours_summary_response(
            intent,
            processed
        )
    # =====================================================
    # DEFAULT FULL SUMMARY
    # =====================================================

    return build_full_alert_summary_response(
        intent,
        alerts,
        processed
    )