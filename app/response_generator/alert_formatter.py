from app.parsers.date_parser import (
    format_time_generate
)
from app.utils.response_utils import build_google_maps_url
from app.utils.logger import logger

from app.response_generator.overspeed_formatter import format_overspeed_summary
from app.response_generator.idling_formatter import format_idling_summary
from app.response_generator.afterhours_formatter import format_afterhours_summary

def build_distribution_text(
    distribution: dict
) -> str:

    if not distribution:
        return ""

    readable_parts = []

    for alert_name, count in distribution.items():

        readable_name = (
            str(alert_name)
            .replace("_", " ")
            .strip()
            .title()
        )

        readable_parts.append(
            f"{count} {readable_name}"
        )

    return ", ".join(readable_parts)


def build_daily_summary_text(
    daily_alerts: dict
) -> str:

    if not daily_alerts:
        return ""

    sorted_days = sorted(
        daily_alerts.items()
    )

    readable_parts = []

    for date, count in sorted_days:

        formatted_date = (
            format_time_generate(date)
            or date
        )

        readable_parts.append(
            f"{formatted_date}: {count}"
        )

    return ", ".join(readable_parts)


def safe_format_date(
    value
) -> str:

    if not value:
        return ""

    try:

        formatted = format_time_generate(value)

        return formatted or str(value)

    except Exception:

        return str(value)


# =========================================================
# ALERT COUNT FORMATTER
# =========================================================

def format_alert_count(
    result,
    intent
):

    total_alerts = result.get(
        "total_alerts",
        0
    )
    
    alert_type_str = "alerts"
    if getattr(intent, "alert_focus", None):
        alert_type_str = f"{intent.alert_focus.replace('_', ' ')} alerts"

    return (
        f"{total_alerts} {alert_type_str} were "
        f"recorded for vehicle "
        f"{intent.vehicle_id}."
    )


# =========================================================
# LATEST ALERT FORMATTER
# =========================================================

def format_latest_alert(
    result,
    intent
):

    latest = result.get(
        "latest_alert",
        {}
    )

    if not latest:

        return (
            f"No latest alert data available "
            f"for vehicle {intent.vehicle_id}."
        )

    latest_parts = []

    alert_name = latest.get(
        "alert_name"
    )

    if alert_name:

        latest_parts.append(
            str(alert_name)
            .replace("_", " ")
            .title()
        )

    latest_time = latest.get(
        "time"
    )

    if latest_time:

        latest_parts.append(
            f"on {safe_format_date(latest_time)}"
        )

    latest_value = latest.get(
        "value"
    )

    if latest_value:

        latest_parts.append(
            f"value {latest_value}"
        )

    latest_limit = latest.get(
        "limit"
    )

    if latest_limit:

        latest_parts.append(
            f"against limit {latest_limit}"
        )

    latest_duration = latest.get(
        "duration"
    )

    if latest_duration:

        latest_parts.append(
            f"lasting {latest_duration}"
        )

    latest_location = latest.get(
    "location"
)

    google_maps_url = build_google_maps_url(
        latest_location
    )

    if google_maps_url:

        latest_parts.append(
            f"location: {google_maps_url}"
        )

    return (
        "Latest alert recorded: "
        + ", ".join(latest_parts)
        + "."
    )


# =========================================================
# DAILY ALERT SUMMARY FORMATTER
# =========================================================

def format_daily_alert_summary(
    result,
    intent
):

    insights = []

    daily_alerts = result.get(
        "daily_alerts",
        {}
    )

    if daily_alerts:

        daily_summary = (
            build_daily_summary_text(
                daily_alerts
            )
        )

        insights.append(
            f"Daily alert trend included "
            f"{daily_summary}"
        )

    peak_day = result.get(
        "peak_alert_day"
    )

    peak_count = result.get(
        "peak_alert_count"
    )

    if peak_day and peak_count:

        insights.append(
            f"Highest alert activity "
            f"occurred on "
            f"{safe_format_date(peak_day)} "
            f"with {peak_count} alerts"
        )

    if not insights:

        return (
            f"No alert summary data available "
            f"for vehicle {intent.vehicle_id}."
        )

    return ". ".join(insights) + "."


# =========================================================
# FULL ALERT SUMMARY FORMATTER
# =========================================================

def format_full_alert_summary(
    result,
    intent
):

    insights = []

    # =====================================================
    # TOTAL ALERTS
    # =====================================================

    total_alerts = result.get(
        "total_alerts",
        0
    )

    insights.append(
        f"Vehicle {intent.vehicle_id} "
        f"recorded {total_alerts} alerts"
    )

    # =====================================================
    # DISTRIBUTION
    # =====================================================

    distribution = result.get(
        "alert_distribution",
        {}
    )

    if distribution:

        distribution_text = (
            build_distribution_text(
                distribution
            )
        )

        insights.append(
            f"Alert distribution included "
            f"{distribution_text}"
        )

    # =====================================================
    # MOST COMMON
    # =====================================================

    most_common_alert = result.get(
        "most_common_alert"
    )

    if most_common_alert:

        readable_alert = (
            str(most_common_alert)
            .replace("_", " ")
            .title()
        )

        insights.append(
            f"Most frequent alert type "
            f"was {readable_alert}"
        )

    # =====================================================
    # DAILY ALERT TREND
    # =====================================================

    daily_alerts = result.get(
        "daily_alerts",
        {}
    )

    if daily_alerts:

        daily_summary = (
            build_daily_summary_text(
                daily_alerts
            )
        )

        insights.append(
            f"Daily alert trend: "
            f"{daily_summary}"
        )

    # =====================================================
    # PEAK ALERT DAY
    # =====================================================

    peak_day = result.get(
        "peak_alert_day"
    )

    peak_count = result.get(
        "peak_alert_count"
    )

    if peak_day and peak_count:

        insights.append(
            f"Peak alert activity occurred "
            f"on {safe_format_date(peak_day)} "
            f"with {peak_count} alerts"
        )

    # =====================================================
    # LATEST ALERT
    # =====================================================

    latest = result.get(
        "latest_alert",
        {}
    )

    if latest:

        latest_parts = []

        alert_name = latest.get(
            "alert_name"
        )

        if alert_name:

            latest_parts.append(
                str(alert_name)
                .replace("_", " ")
                .title()
            )

        latest_time = latest.get(
            "time"
        )

        if latest_time:

            latest_parts.append(
                f"on {safe_format_date(latest_time)}"
            )

        latest_value = latest.get(
            "value"
        )

        if latest_value:

            latest_parts.append(
                f"value {latest_value}"
            )

        latest_limit = latest.get(
            "limit"
        )

        if latest_limit:

            latest_parts.append(
                f"against limit {latest_limit}"
            )

        latest_duration = latest.get(
            "duration"
        )

        if latest_duration:

            latest_parts.append(
                f"lasting {latest_duration}"
            )

        latest_location = latest.get(
            "location"
        )

        google_maps_url = build_google_maps_url(
            latest_location
        )

        if google_maps_url:

            latest_parts.append(
                f"location: {google_maps_url}"
            )

        if latest_parts:

            insights.append(
                "Latest alert recorded: "
                + ", ".join(latest_parts)
            )

    # =====================================================
    # OVERSPEED
    # =====================================================

    overspeed = result.get(
        "overspeed",
        {}
    )

    overspeed_count = overspeed.get(
        "count",
        0
    )

    if overspeed_count:

        insights.append(
            f"{overspeed_count} overspeed "
            f"alerts were detected"
        )

        highest = overspeed.get(
            "highest"
        )

        if highest:

            highest_parts = []

            highest_speed = highest.get(
                "speed"
            )

            if highest_speed:

                highest_parts.append(
                    f"highest speed reached "
                    f"{highest_speed}"
                )

            highest_limit = highest.get(
                "limit"
            )

            if highest_limit:

                highest_parts.append(
                    f"against limit "
                    f"{highest_limit}"
                )

            highest_time = highest.get(
                "time"
            )

            if highest_time:

                highest_parts.append(
                    f"on "
                    f"{safe_format_date(highest_time)}"
                )

            highest_duration = highest.get(
                "duration"
            )

            if highest_duration:

                highest_parts.append(
                    f"lasting "
                    f"{highest_duration}"
                )

            highest_location = highest.get(
                "location"
            )

            google_maps_url = build_google_maps_url(
                highest_location
            )

            if google_maps_url:

                highest_parts.append(
                    f"location: {google_maps_url}"
                )
                

            if highest_parts:

                insights.append(
                    "Highest overspeed event: "
                    + ", ".join(highest_parts)
                )

    else:

        insights.append(
            "No overspeed alerts were detected"
        )

    # =====================================================
    # IDLING
    # =====================================================

    idling = result.get(
        "idling",
        {}
    )

    idling_count = idling.get(
        "count",
        0
    )

    if idling_count:

        insights.append(
            f"{idling_count} idling "
            f"alerts were detected"
        )

        longest_idle = idling.get(
            "longest"
        )

        if longest_idle:

            idle_parts = []

            idle_duration = longest_idle.get(
                "duration"
            )

            if idle_duration:

                idle_parts.append(
                    f"longest idle duration "
                    f"was {idle_duration}"
                )

            idle_time = longest_idle.get(
                "time"
            )

            if idle_time:

                idle_parts.append(
                    f"on "
                    f"{safe_format_date(idle_time)}"
                )

            idle_location = longest_idle.get(
                "location"
            )

            if idle_location:

                idle_parts.append(
                    f"at location "
                    f"{idle_location}"
                )

            if idle_parts:

                insights.append(
                    "Longest idling event: "
                    + ", ".join(idle_parts)
                )

    else:

        insights.append(
            "No idling alerts were detected"
        )

    # =====================================================
    # AFTER HOURS MOVEMENT
    # =====================================================

    afterhours = result.get(
        "afterhoursmovement",
        {}
    )

    afterhours_count = afterhours.get(
        "count",
        0
    )

    if afterhours_count:

        insights.append(
            f"{afterhours_count} "
            f"after-hours movement "
            f"alerts were detected"
        )

    else:

        insights.append(
            "No after-hours movement "
            "alerts were detected"
        )

    return ". ".join(insights) + "."


# Detailed summary formatters have been moved to separate module files for improved readability.



# =========================================================
# TIME RANGE CONTEXT LINE
# =========================================================

def build_time_range_context(intent) -> str:
    """
    Returns a human-readable period line.
    e.g. "Data covers today (2026-05-25)."
         "Data covers the last 7 days (2026-05-18 to 2026-05-25)."
    """

    time_range = getattr(intent, "time_range", None)
    if not time_range or len(time_range) != 2:
        return ""

    from_date, to_date = time_range

    if from_date == to_date:
        return f"Data covers today ({to_date})"

    try:
        from datetime import datetime
        dt_from = datetime.strptime(from_date, "%Y-%m-%d")
        dt_to = datetime.strptime(to_date, "%Y-%m-%d")
        days = (dt_to - dt_from).days
        if days == 1:
            return f"Data covers the last day ({from_date} to {to_date})"
        return f"Data covers the last {days} days ({from_date} to {to_date})"
    except Exception:
        return f"Data covers the period from {from_date} to {to_date}"


# =========================================================
# MAIN ROUTER
# =========================================================

def format_alert(
    result,
    intent
):

    result_type = result.get("type")

    # ERROR
    if result_type == "error":
        return result.get(
            "message",
            "Unable to process alert data."
        )

    # Dispatch to specific formatter to get base message
    if result_type == "alert_count":
        base_msg = format_alert_count(result, intent)
    elif result_type == "latest_alert":
        base_msg = format_latest_alert(result, intent)
    elif result_type == "daily_alert_summary":
        base_msg = format_daily_alert_summary(result, intent)
    elif result_type == "alert_summary":
        base_msg = format_full_alert_summary(result, intent)
    elif result_type == "overspeed_summary":
        base_msg = format_overspeed_summary(result, intent)
    elif result_type == "idling_summary":
        base_msg = format_idling_summary(result, intent)
    elif result_type == "afterhours_summary":
        base_msg = format_afterhours_summary(result, intent)
    else:
        return "Unable to format alert response."

    # Prepend time range context if applicable
    context_line = build_time_range_context(intent)
    if context_line:
        return f"{context_line}. {base_msg}"

    return base_msg