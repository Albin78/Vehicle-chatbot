import numpy as np

from app.utils.response_utils import error_response


SUPPORTED_METRICS = {
    "speed": "maxSpeed",
    "distance": "distance",
    "distance_travelled": "distance",
    "idle_time": "idleTime",
    "moving_time": "movingTime",
    "stop_time": "stopTime"
}


def parse_time_str(time_val):
    if time_val is None:
        return 0
    val_str = str(time_val)
    if ":" in val_str:
        try:
            parts = val_str.split(":")
            if len(parts) >= 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
        except Exception:
            pass
    try:
        return float(time_val)
    except Exception:
        return 0

def format_seconds(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def compute_metric(rows, metric, aggregation, query_string=""):

    field = SUPPORTED_METRICS.get(metric)

    if not field:
        return None

    values = []
    
    is_time_metric = metric in ["idle_time", "moving_time", "stop_time"]

    for row in rows:

        value = row.get(field)

        if value is None:
            continue

        if field == "distance":
            value = float(value)
        elif is_time_metric:
            value = parse_time_str(value)

        values.append(value)

    if not values:
        return None

    specific_agg = aggregation
    if query_string:
        q = query_string.lower()
        metric_words = metric.replace("_", " ")
        
        if f"average {metric_words}" in q or f"avg {metric_words}" in q:
            specific_agg = "average"
        elif f"highest {metric_words}" in q or f"max {metric_words}" in q or f"maximum {metric_words}" in q:
            specific_agg = "maximum"
        elif f"total {metric_words}" in q:
            specific_agg = "total"
            
        if metric == "speed":
            if "average speed" in q: specific_agg = "average"
            elif "highest speed" in q or "max speed" in q: specific_agg = "maximum"
            
        if metric in ["distance", "distance_travelled"]:
            if "average distance" in q: specific_agg = "average"
            elif "total distance" in q: specific_agg = "total"

    # Determine default behavior
    # BUG FIX: result_date was only assigned inside maximum/minimum/average/else
    # branches but NOT in the distance/idle_time sum branches, causing an
    # UnboundLocalError crash when aggregation is None for time-metric queries.
    result_date = None   # safe default — overridden where a date is meaningful
    if metric in ["distance", "distance_travelled"] and specific_agg != "average":
        result = sum(values)
        if specific_agg not in ["maximum", "minimum"]:
            specific_agg = "total"
    elif is_time_metric and specific_agg != "average":
        result = sum(values)
        if specific_agg not in ["maximum", "minimum"]:
            specific_agg = "total"
    elif specific_agg == "maximum":
        max_idx = values.index(max(values))
        result = values[max_idx]
        result_date = rows[max_idx].get("Date") or rows[max_idx].get("ReportDate") or rows[max_idx].get("DateString")
    elif specific_agg == "minimum":
        min_idx = values.index(min(values))
        result = values[min_idx]
        result_date = rows[min_idx].get("Date") or rows[min_idx].get("ReportDate") or rows[min_idx].get("DateString")
    elif specific_agg == "average":
        result = sum(values) / len(values)
    else:
        result = sum(values) if specific_agg == "total" else values[-1]
        
    if is_time_metric:
        val = format_seconds(result)
    else:
        val = round(result, 2)
        
    return {"value": val, "aggregation": specific_agg, "date": result_date}


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

        metrics_data = {}
        metric_aggregations = {}
        metric_dates = {}
        query_str = getattr(intent, "query", "") or ""
        
        for m in intent.metrics:
            if m in SUPPORTED_METRICS:
                res = compute_metric(rows, m, intent.aggregation, query_str)
                if res is not None:
                    metrics_data[m] = res["value"]
                    metric_aggregations[m] = res["aggregation"]
                    if res.get("date"):
                        metric_dates[m] = res["date"]

        # Only return a metric summary if we actually computed at least one metric
        if metrics_data and not intent.summary_requested:
            return {

                "type": "summary_metric",

                "vehicle":
                    intent.vehicle_id,

                "metrics": metrics_data,
                "metric_aggregations": metric_aggregations,
                "metric_dates": metric_dates,

                "aggregation":
                    intent.aggregation,

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