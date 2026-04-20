import numpy as np


def build_execution_plan(intent):

    return {
        "need_vehicle": intent.vehicle_id is not None,
        "need_summary": intent.metric is None and intent.time_range is not None,
        "need_metric": intent.metric is not None,
        "metric": intent.metric,
        "aggregation": intent.aggregation
    }



def compute_metric(rows, metric, aggregation=None):
    if not rows:
        return None

    if metric == "speed":
        values = [r.get("maxSpeed", 0) for r in rows]

    elif metric == "distance":
        values = [float(r.get("distance", 0)) for r in rows]

    elif metric == "idleTime":
        values = [r.get("idleTime", 0) for r in rows]

    else:
        return None

    if not values:
        return None

    if aggregation == "maximum":
        return round(max(values), 2)

    elif aggregation == "minimum":
        return round(min(values),2)

    elif aggregation == "average":
        return round(sum(values) / len(values),2)

    else:
        return values[-1]  
    



def extract_summary(summary):
    return {
        "total_distance": summary.get("totalDistance"),
        "total_moving_time": summary.get("totalMovingTime"),
        "total_idle_time": summary.get("totalIdleTime"),
        "total_stop_time": summary.get("totalStopTime"),
        "engine_hours": summary.get("totalEngineHours")
    }


def compute_derived(rows):
    speeds = [row.get("maxSpeed", 0) for row in rows]
    averages = [r.get("maxSpeed", 0) for r in rows]
    return {
        "max_speed": max(speeds, default=0),
        "average_speed": float(np.mean(averages))
    }



def build_response(intent, api_result):

    rows = api_result.get("dataRows", [])
    summary = api_result.get("summary", {})

    plan = build_execution_plan(intent)

    
    # CASE 1: METRIC QUERY
    # -----------------------------
    if plan["need_metric"]:
        value = compute_metric(rows, plan["metric"], plan["aggregation"])

        return {
            "type": "metric",
            "metric": plan["metric"],
            "aggregation": plan["aggregation"] or "current",
            "value": value
        }

    
    # CASE 2: DETAILS QUERY
    # -----------------------------
    response = {
        "type": "summary",
        "vehicle_type": rows[0].get("type"),
        "group": rows[0].get("groupName")
    }

    if plan["need_summary"]:
        response.update(extract_summary(summary))

    # Add derived insights ALWAYS for details
    response.update(compute_derived(rows))

    return response