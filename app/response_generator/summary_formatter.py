from app.parsers.date_parser import format_time_generate


METRIC_UNITS = {
    "speed": "km/h",
    "distance": "km"
}


def format_summary(result, intent):

    result_type = result.get("type")

    # =====================================
    # SUMMARY METRIC RESPONSE
    # =====================================

    if result_type == "summary_metric":

        metric = result.get("metric")

        aggregation = result.get("aggregation")

        value = result.get("value")

        unit = METRIC_UNITS.get(metric, "")

        from_date, to_date = result.get(
            "time_range",
            ("", "")
        )

        return (
            f"For vehicle {result.get('vehicle')}, "
            f"the {aggregation} {metric} "
            f"between {from_date} and {to_date} "
            f"was {value} {unit}."
        )

    # =====================================
    # FULL SUMMARY RESPONSE
    # =====================================

    summary = result.get("summary", {})

    analytics = result.get("analytics", {})

    daily_reports = result.get(
        "daily_reports",
        []
    )

    from_date, to_date = result.get(
        "time_range",
        ("", "")
    )

    parts = []

    # -------------------------------------
    # Vehicle Context
    # -------------------------------------

    parts.append(

        f"Vehicle {result.get('vehicle')} "

        f"of type {result.get('vehicle_type')} "

        f"belongs to group {result.get('group')}"

    )

    # -------------------------------------
    # Time Range
    # -------------------------------------

    if from_date and to_date:

        parts.append(

            f"for the period from "
            f"{from_date} to {to_date}"

        )

    # -------------------------------------
    # Operational Summary
    # -------------------------------------

    if summary.get("total_distance"):

        parts.append(

            f"total distance traveled was "
            f"{summary.get('total_distance')} km"

        )

    if summary.get("total_moving_time"):

        parts.append(

            f"total moving time was "
            f"{summary.get('total_moving_time')}"

        )

    if summary.get("total_idle_time"):

        parts.append(

            f"total idle time was "
            f"{summary.get('total_idle_time')}"

        )

    if summary.get("total_stop_time"):

        parts.append(

            f"total stop time was "
            f"{summary.get('total_stop_time')}"

        )

    if summary.get("total_engine_hours"):

        parts.append(

            f"total engine hours were "
            f"{summary.get('total_engine_hours')}"

        )

    # -------------------------------------
    # Analytics
    # -------------------------------------

    if analytics.get("highest_speed"):

        parts.append(

            f"highest speed recorded was "
            f"{analytics.get('highest_speed')} km/h "
            f"on "
            f"{analytics.get('highest_speed_day')}"

        )

    if analytics.get("average_speed"):

        parts.append(

            f"average daily maximum speed across "
            f"{analytics.get('total_days')} days "
            f"was "
            f"{analytics.get('average_speed')} km/h"

        )

    if analytics.get("longest_distance"):

        parts.append(

            f"the longest distance covered in a single day "
            f"was "
            f"{analytics.get('longest_distance')} km "
            f"on "
            f"{analytics.get('longest_distance_day')}"

        )

    # -------------------------------------
    # Daily Breakdown (Production Important)
    # -------------------------------------

    if len(daily_reports) <= 5:

        for report in daily_reports:

            parts.append(

                f"on {report.get('date')}, "

                f"distance traveled was "
                f"{report.get('distance')} km "

                f"with maximum speed "
                f"{report.get('max_speed')} km/h, "

                f"moving time "
                f"{report.get('moving_time')}, "

                f"idle time "
                f"{report.get('idle_time')} "

                f"and stop time "
                f"{report.get('stop_time')}"

            )

    return ". ".join(parts) + "."