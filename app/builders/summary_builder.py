import numpy as np

from app.utils.response_utils import error_response


SUPPORTED_METRICS = {
    "speed": "maxSpeed",
    "distance": "distance",
    "idle_time": "idleTime",
    "moving_time": "movingTime",
    "stop_time": "stopTime"
}


def compute_metric(rows, metric, aggregation):

    field = SUPPORTED_METRICS.get(metric)

    if not field:
        return None

    values = []

    for row in rows:

        value = row.get(field)

        if value is None:
            continue

        if field == "distance":
            value = float(value)

        values.append(value)

    if not values:
        return None

    if aggregation == "maximum":
        return round(max(values), 2)

    if aggregation == "minimum":
        return round(min(values), 2)

    if aggregation == "average":
        return round(sum(values) / len(values), 2)

    return round(values[-1], 2)


def build_daily_reports(rows):

    reports = []

    for row in rows:

        reports.append({

            "date": row.get("Date"),

            "distance": float(
                row.get("distance", 0)
            ),

            "max_speed": row.get("maxSpeed"),

            "moving_time":
                row.get("movingTimeFormated"),

            "idle_time":
                row.get("idleTimeFormated"),

            "stop_time":
                row.get("stopTimeFormated"),

            "first_active":
                row.get("firstActiveTime"),

            "last_active":
                row.get("lastActiveTime")
        })

    return reports


def build_analytics(rows):

    if not rows:
        return {}

    highest_speed_row = max(
        rows,
        key=lambda r: r.get("maxSpeed", 0)
    )

    longest_distance_row = max(
        rows,
        key=lambda r: float(
            r.get("distance", 0)
        )
    )

    total_distance = sum(
        float(r.get("distance", 0))
        for r in rows
    )

    average_speed = np.mean([
        r.get("maxSpeed", 0)
        for r in rows
    ])

    return {

        "total_days": len(rows),

        "overall_distance":
            round(total_distance, 2),

        "average_speed":
            round(float(average_speed), 2),

        "highest_speed":
            highest_speed_row.get("maxSpeed"),

        "highest_speed_day":
            highest_speed_row.get("Date"),

        "longest_distance":
            longest_distance_row.get("distance"),

        "longest_distance_day":
            longest_distance_row.get("Date")
    }


def build_summary_response(intent, api_result):

    operation_summary = api_result.get(
        "operationSummary"
    )

    if not operation_summary:
        return error_response(
            "Operation summary not available"
        )

    rows = operation_summary.get(
        "dataRows",
        []
    )

    summary = operation_summary.get(
        "summary",
        {}
    )

    if not rows:
        return error_response(
            "No operation summary found"
        )

    # -----------------------------
    # METRIC QUERY
    # -----------------------------

    if intent.metrics:

        metric = intent.metrics[0]

        value = compute_metric(
            rows,
            metric,
            intent.aggregation
        )

        return {

            "type": "summary_metric",

            "vehicle":
                intent.vehicle_id,

            "metric": metric,

            "aggregation":
                intent.aggregation,

            "value": value,

            "time_range":
                intent.time_range
        }

    # -----------------------------
    # FULL SUMMARY QUERY
    # -----------------------------

    return {

        "type": "summary",

        "vehicle":
            intent.vehicle_id,

        "vehicle_type":
            rows[0].get("type"),

        "group":
            rows[0].get("groupName"),

        "summary": {

            "total_distance":
                summary.get("totalDistance"),

            "total_moving_time":
                summary.get("totalMovingTime"),

            "total_idle_time":
                summary.get("totalIdleTime"),

            "total_stop_time":
                summary.get("totalStopTime"),

            "total_engine_hours":
                summary.get("totalEngineHours")
        },

        "analytics":
            build_analytics(rows),

        "daily_reports":
            build_daily_reports(rows),

        "time_range":
            intent.time_range
    }