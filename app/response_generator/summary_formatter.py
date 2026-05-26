from app.parsers.date_parser import (
    format_time_generate
)
from app.utils.logger import logger

# =========================================================
# CONFIG
# =========================================================

MAX_DAILY_REPORTS = 5


METRIC_UNITS = {

    "speed": "km/h",
    "distance": "km"

}


# =========================================================
# HELPERS
# =========================================================

def safe_format_date(value):

    if not value:
        return ""

    formatted = format_time_generate(value)

    return formatted or str(value)


def clean_group_name(group_name: str) -> str:

    if not group_name:
        return ""

    ignored = {

        "others",
        "info",
        "test group"

    }

    cleaned = [

        item.strip()

        for item in group_name.split(",")

        if item.strip().lower() not in ignored

    ]

    return ", ".join(cleaned)


# =========================================================
# VEHICLE CONTEXT
# =========================================================

def build_vehicle_context(result):

    vehicle = result.get("vehicle")

    vehicle_type = result.get("vehicle_type")

    group = clean_group_name(
        result.get("group", "")
    )

    parts = []

    if vehicle:

        parts.append(
            f"Vehicle {vehicle}"
        )

    if vehicle_type:

        parts.append(
            f"of type {vehicle_type}"
        )

    if group:

        parts.append(
            f"belongs to group {group}"
        )

    return " ".join(parts)


# =========================================================
# TIME CONTEXT
# =========================================================

def build_time_context(result):

    time_range = result.get(
        "time_range"
    )

    if not time_range:
        return ""

    formatted = format_time_generate(
        time_range
    )

    if not formatted:
        return ""

    return (
        f"For the period "
        f"{formatted}"
    )


# =========================================================
# OPERATIONAL SUMMARY
# =========================================================

def build_operational_summary(summary):

    if not summary:
        return ""

    parts = []

    if summary.get("total_distance"):

        parts.append(

            f"Total distance traveled was "
            f"{summary.get('total_distance')} km"

        )

    if summary.get("total_moving_time"):

        parts.append(

            f"Total moving time was "
            f"{summary.get('total_moving_time')}"

        )

    if summary.get("total_idle_time"):

        parts.append(

            f"Total idle time was "
            f"{summary.get('total_idle_time')}"

        )

    if summary.get("total_stop_time"):

        parts.append(

            f"Total stop time was "
            f"{summary.get('total_stop_time')}"

        )

    if summary.get("total_engine_hours"):

        parts.append(

            f"Total engine hours were "
            f"{summary.get('total_engine_hours')}"

        )

    return ". ".join(parts)


# =========================================================
# ANALYTICS SUMMARY
# =========================================================

def build_analytics_summary(analytics):

    if not analytics:
        return ""

    parts = []

    highest_speed = analytics.get(
        "highest_speed"
    )

    if highest_speed:

        highest_day = safe_format_date(
            analytics.get(
                "highest_speed_day"
            )
        )

        parts.append(

            f"Highest speed recorded was "
            f"{highest_speed} km/h "
            f"on {highest_day}"

        )

    average_speed = analytics.get(
        "average_speed"
    )

    if average_speed:

        total_days = analytics.get(
            "total_days"
        )

        parts.append(

            f"Average daily maximum speed "
            f"across {total_days} days "
            f"was {average_speed} km/h"

        )

    longest_distance = analytics.get(
        "longest_distance"
    )

    if longest_distance:

        longest_day = safe_format_date(
            analytics.get(
                "longest_distance_day"
            )
        )

        parts.append(

            f"The longest distance covered "
            f"in a single day was "
            f"{longest_distance} km "
            f"on {longest_day}"

        )

    return ". ".join(parts)


# =========================================================
# DAILY BREAKDOWN
# =========================================================

def build_daily_breakdown(daily_reports):

    if not daily_reports:
        return ""

    parts = []

    for report in daily_reports:

        report_date = safe_format_date(
            report.get("date")
        )

        parts.append(

            f"On {report_date}, "
            f"distance traveled was "
            f"{report.get('distance')} km, "
            f"maximum speed reached "
            f"{report.get('max_speed')} km/h, "
            f"moving time was "
            f"{report.get('moving_time')}, "
            f"idle time was "
            f"{report.get('idle_time')}, "
            f"and stop time was "
            f"{report.get('stop_time')}"

        )

    return ". ".join(parts)


# =========================================================
# SUMMARY METRIC FORMATTER
# =========================================================

def format_summary_metric(result):

    metric = result.get("metric")

    aggregation = result.get(
        "aggregation"
    )

    value = result.get("value")

    unit = METRIC_UNITS.get(
        metric,
        ""
    )

    formatted_range = format_time_generate(
        result.get("time_range")
    )

    return (

        f"For vehicle "
        f"{result.get('vehicle')}, "
        f"the {aggregation} {metric} "
        f"during {formatted_range} "
        f"was {value} {unit}."

    )


# =========================================================
# MAIN FORMATTER
# =========================================================

def format_summary(result, intent):

    result_type = result.get("type")

    # =====================================
    # SUMMARY METRIC
    # =====================================

    if result_type == "summary_metric":

        return format_summary_metric(
            result
        )

    # =====================================
    # FULL SUMMARY
    # =====================================

    sections = []

    vehicle_context = (
        build_vehicle_context(result)
    )

    if vehicle_context:

        sections.append(
            vehicle_context
        )

    time_context = (
        build_time_context(result)
    )

    if time_context:

        sections.append(
            time_context
        )

    operational_summary = (
        build_operational_summary(
            result.get("summary", {})
        )
    )

    if operational_summary:

        sections.append(
            operational_summary
        )

    analytics_summary = (
        build_analytics_summary(
            result.get("analytics", {})
        )
    )

    if analytics_summary:

        sections.append(
            analytics_summary
        )

    daily_breakdown = (
        build_daily_breakdown(
            result.get(
                "daily_reports",
                []
            )
        )
    )

    if daily_breakdown:

        sections.append(
            daily_breakdown
        )

    if not sections:

        return (
            "No summary data available."
        )

    return ". ".join(sections) + "."