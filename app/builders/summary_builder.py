import numpy as np
from app.utils.response_utils import error_response



def extract_summary(operation_summary):

    return operation_summary.get(
        "summary",
        {}
    )


def build_daily_analysis(rows):

    if not rows:
        return {}

    max_speed_row = max(
        rows,
        key=lambda r: r.get("maxSpeed", 0)
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

        "overall_distance": round(
            total_distance,
            2
        ),

        "average_speed": round(
            float(average_speed),
            2
        ),

        "highest_speed": max_speed_row.get(
            "maxSpeed"
        ),

        "highest_speed_day": max_speed_row.get(
            "Date"
        ),

        "daily_reports": [

            {
                "date": row.get("Date"),

                "distance": row.get("distance"),

                "max_speed": row.get("maxSpeed"),

                "moving_time":
                    row.get("movingTimeFormated"),

                "idle_time":
                    row.get("idleTimeFormated"),

                "stop_time":
                    row.get("stopTimeFormated")
            }

            for row in rows
        ]
    }



def compute_metric(rows, metric, aggregation):

    if metric == "speed":

        values = [
            r.get("maxSpeed", 0)
            for r in rows
        ]

    elif metric == "distance":

        values = [
            float(r.get("distance", 0))
            for r in rows
        ]

    else:
        return None

    if aggregation == "maximum":
        return max(values)

    if aggregation == "minimum":
        return min(values)

    if aggregation == "average":
        return round(sum(values) / len(values), 2)

    return values[-1]



def build_summary_response(intent, api_result):

    operation = api_result.get(
        "operationSummary",
        {}
    )

    rows = operation.get(
        "dataRows",
        []
    )

    summary = operation.get(
        "summary",
        {}
    )

    if not rows:
        return error_response(
            "No operation summary found"
        )

    if intent.metric:

        value = compute_metric(
            rows,
            intent.metric,
            intent.aggregation
        )

        return {
            "type": "summary_metric",

            "metric": intent.metric,

            "aggregation": intent.aggregation,

            "value": value
        }

    analytics = build_daily_analysis(rows)

    return {

        "type": "summary",

        "vehicle": intent.vehicle_id,

        "summary": summary,

        "analytics": analytics,

        "vehicle_type": rows[0].get("type"),

        "group": rows[0].get("groupName")
    }