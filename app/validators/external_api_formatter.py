import numpy as np
from datetime import datetime
from typing import Dict

from app.tools.vehicle_resolver import normalize_vehicle_id
from app.utils.logger import logger



REALTIME_METRIC_MAP = {
    "speed": "speed",
    "weight": "Weight",
    "fuel_capacity": "fuelCapacity",
    "tanker_fuel_capacity": "TankerfuelCapacity",
    "battery": "batteryLevel",
    "fuel_level": "fuelLevel"
}

def detect_alert_analysis(query: str) -> str:
    q = query.lower()

    has_latest = any(w in q for w in ["latest", "last", "recent"])
    has_count = any(w in q for w in ["how many", "count", "total", "number of"])
    has_summary = any(w in q for w in ["report", "summary", "overview", "details"])

    # Priority logic (IMPORTANT)
    if has_count:
        return "count"

    if has_latest and not has_summary:
        return "latest"

    if has_summary:
        return "summary"

    # fallback
    return "summary"



def build_execution_plan(intent):
    return {
        "intent_type": intent.intent_type, 
        "need_vehicle": intent.vehicle_id is not None,
        "need_summary": intent.metric is None and intent.time_range is not None,
        "need_metric": intent.metric is not None,
        "metric": intent.metric,
        "aggregation": intent.aggregation
    }

def error_response(message):
    return {
        "type": "error",
        "message": message
    }


def filter_vehicle_from_realtime(data, vehicle_id):
    normalized_input = normalize_vehicle_id(vehicle_id)
    logger.info(f"Normalized vehicle id using normalize function: {normalized_input}")

    for record in data:
        plate = normalize_vehicle_id(record.get("numberPlate"))
        if plate == normalized_input:
            return record
    return None

def build_realtime_metric_response(vehicle, metric):

    if metric not in REALTIME_METRIC_MAP:
        return error_response(f"Unsupported metric: {metric}")

    field = REALTIME_METRIC_MAP[metric]
    value = vehicle.get(field)

    return {
        "type": "realtime_metric",
        "vehicle": vehicle.get("numberPlate"),
        "metric": metric,
        "available": value is not None,
        "value": value
    }


def derive_vehicle_status(record):
    vstatus_map = {
        1: "Moving",
        2: "Idle",
        3: "Stopped",
        4: "Disconnected"
    }

    vstatus = record.get("vStatus")

    # Priority 1: Use API truth
    if vstatus in vstatus_map:
        return vstatus_map[vstatus]

    # Fallback (if vStatus missing)
    speed = record.get("speed", 0)
    ignition = record.get("ignitionOn", 0)

    if speed > 0:
        return "Moving"
    elif ignition == 1:
        return "Idle"
    else:
        return "Stopped"


def build_realtime_status_response(vehicle):

    response = {
        "type": "realtime_status",
        "vehicle": vehicle.get("numberPlate"),
        "status": derive_vehicle_status(vehicle),
        "last_updated": vehicle.get("lastUpdatedTime")
    }

    optional_fields = {
        "speed": vehicle.get("speed"),
        "battery_level": vehicle.get("batteryLevel"),
        "fuel_capacity": vehicle.get("fuelCapacity"),
        "fuel_level": vehicle.get("fuelLevel"),
        "tanker_fuel_capacity": vehicle.get("TankerfuelCapacity"),
        "weight": vehicle.get("Weight"),
        "mileage": vehicle.get("mileage"),
        "driver": vehicle.get("driverName")
    }

    # Include ONLY non-null fields
    response.update(optional_fields)

    return response



def build_realtime_response(intent, api_result):

    records = api_result.get("data", [])

    if not records:
        return error_response("No realtime data is currently available for this vehicle. Please try again shortly or verify the vehicle ID.")

    vehicle = filter_vehicle_from_realtime(records, intent.vehicle_id)

    if not vehicle:
        return error_response("Vehicle not found or may be mismatch in vehicle id given or extraction.")

    if intent.metric is not None:
        return build_realtime_metric_response(vehicle, intent.metric)

    return build_realtime_status_response(vehicle)


def parse_date(date_str):
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def build_alert_response(intent, api_result):
    alerts = api_result.get("results", [])

    if not alerts:
        return error_response(f"No alerts found for vehicle id {intent.vehicle_id} in the given time range.")

    alerts_sorted = sorted(
        alerts,
        key=lambda x: parse_date(x.get("Date")),
        reverse=True
    )

    analysis = intent.analysis or "summary"

    # -----------------------------
    # LATEST
    # -----------------------------
    if analysis == "latest":
        latest = alerts_sorted[0]

        return {
            "type": "alert_latest",
            "alert_name": latest.get("AlertName"),
            "time": latest.get("Date"),
            "driver": latest.get("DriverName"),
            "value": latest.get("CurrentValue"),
            "duration": latest.get("Duration"),
            "limit": latest.get("Limit")
        }

    # -----------------------------
    # COUNT
    # -----------------------------
    if analysis == "count":
        return {
            "type": "alert_count",
            "total_alerts": len(alerts)
        }

    # -----------------------------
    # SUMMARY
    # -----------------------------
    total_alerts = len(alerts)

    
    alert_types: Dict[str, int] = {}
    max_value = 0
    max_event = None

    for alert in alerts:
        name = alert.get("AlertName")
        
        if not name:
            continue

        alert_types[name] = alert_types.get(name, 0) + 1

        value = alert.get("OrginalValue", 0)
        if value > max_value:
            max_value = value
            max_event = alert

    most_common = max(alert_types, key=lambda k: alert_types.get(k, 0))
    latest = alerts_sorted[0]

    return {
        "type": "alert_summary",
        "total_alerts": total_alerts,
        "most_common_alert": most_common,
        "latest_alert": {
            "alert_name": latest.get("AlertName"),
            "time": latest.get("Date"),
            "driver": latest.get("DriverName"),
            "current_value": latest.get("CurrentValue"),
            "duration": latest.get("Duration"),
            "limit": latest.get("Limit") 
        },
        "peak_alert": {
            "alert_name": max_event.get("AlertName") if max_event else None,
            "value": max_event.get("CurrentValue") if max_event else None,
            "time": max_event.get("Date") if max_event else None,
            "limit": max_event.get("Limit") if max_event else None
        }
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
        "average_speed": float(np.mean(averages)),
        "minimum_speed": min(speeds, default=0)
    }


def build_response(intent, api_result):

    # -----------------------------
    # REALTIME
    # -----------------------------
    if intent.intent_type == "realtime":
        return build_realtime_response(intent, api_result)
    
    # Alert
    if intent.intent_type == "alert":
        return build_alert_response(intent, api_result)
    # -----------------------------
    # HISTORICAL
    # -----------------------------
    rows = api_result.get("dataRows", [])
    summary = api_result.get("summary", {})

    if not rows:
        return error_response("No data found")

    plan = build_execution_plan(intent)

    # -----------------------------
    # METRIC
    # -----------------------------
    if plan["need_metric"]:
        value = compute_metric(rows, plan["metric"], plan["aggregation"])

        return {
            "type": "metric",
            "metric": plan["metric"],
            "aggregation": plan["aggregation"],
            "value": value
        }

    # -----------------------------
    # SUMMARY
    # -----------------------------
    response = {
        "type": "summary",
        "vehicle_type": rows[0].get("type"),
        "group": rows[0].get("groupName")
    }

    if plan["need_summary"]:
        response.update(extract_summary(summary))

    response.update(compute_derived(rows))

    return response