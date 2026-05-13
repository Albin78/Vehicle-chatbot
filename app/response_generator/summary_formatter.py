from app.parsers.date_parser import format_time_generate


def format_summary(result, intent):

    result_type = result.get("type")

    # -------------------------
    # SUMMARY METRIC
    # -------------------------

    if result_type == "summary_metric":

        metric = result.get("metric")
        aggregation = result.get("aggregation")
        value = result.get("value")

        return (
            f"For vehicle {intent.vehicle_id}, "
            f"the {aggregation} {metric} "
            f"for the selected time range "
            f"is {value}."
        )

    # -------------------------
    # SUMMARY
    # -------------------------

    summary = result.get("summary", {})
    analytics = result.get("analytics", {})

    parts = []

    parts.append(
        f"Vehicle {result.get('vehicle')} "
        f"of type {result.get('vehicle_type')} "
        f"belongs to group {result.get('group')}"
    )

    if summary.get("totalDistance"):
        parts.append(
            f"total distance traveled was "
            f"{summary.get('totalDistance')} km"
        )

    if summary.get("totalMovingTime"):
        parts.append(
            f"total moving time was "
            f"{summary.get('totalMovingTime')}"
        )

    if summary.get("totalIdleTime"):
        parts.append(
            f"total idle time was "
            f"{summary.get('totalIdleTime')}"
        )

    if summary.get("totalEngineHours"):
        parts.append(
            f"engine hours were "
            f"{summary.get('totalEngineHours')}"
        )

    if analytics.get("highest_speed"):

        parts.append(
            f"highest speed recorded was "
            f"{analytics.get('highest_speed')} km/h "
            f"on "
            f"{analytics.get('highest_speed_day')}"
        )

    if analytics.get("average_speed"):

        parts.append(
            f"average maximum speed across "
            f"{analytics.get('total_days')} days "
            f"was "
            f"{analytics.get('average_speed')} km/h"
        )

    return ". ".join(parts) + "."