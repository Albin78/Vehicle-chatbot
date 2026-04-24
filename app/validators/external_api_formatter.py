import numpy as np
from app.tools.vehicle_resolver import normalize_vehicle_id

def build_execution_plan(intent):
    return {
        "intent_type": intent.intent_type, 
        "need_vehicle": intent.vehicle_id is not None,
        "need_summary": intent.metric is None and intent.time_range is not None,
        "need_metric": intent.metric is not None,
        "metric": intent.metric,
        "aggregation": intent.aggregation
    }


def filter_vehicle_from_realtime(data, vehicle_id=None):
    
        
    for record in data:
        if record.get("numberPlate", "").replace(" ", "") == vehicle_id:
            return record
    return None


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


def build_realtime_base(vehicle):
    return {
        "vehicle": vehicle.get("numberPlate"),
        "status": derive_vehicle_status(vehicle),
        "speed": vehicle.get("speed"),
        "battery": vehicle.get("batteryLevel"),
        "fuel_capacity": vehicle.get("fuelCapacity"),
        "tanker_fuel_capacity": vehicle.get("TankerfuelCapacity"),
        "weight": vehicle.get("Weight"),
        "driver": vehicle.get("driverName"),
        "location": {
            "lat": vehicle.get("lat"),
            "lon": vehicle.get("lon")
        }
    }

def build_realtime_response(intent, api_result):

    records = api_result.get("data", [])

    vehicle = filter_vehicle_from_realtime(
        records,
        vehicle_id=intent.vehicle_id
    )

    if not vehicle:
        return {"error": "Vehicle not found"}

    if intent.metric:
        field = REALTIME_METRIC_MAP.get(intent.metric)

        if not field:
            return {"error": f"Unsupported metric: {intent.metric}"}

        return {
            "type": "realtime_metric",
            "vehicle": vehicle.get("numberPlate"),
            "metric": intent.metric,
            "value": vehicle.get(field)
        }

    if intent.intent_type == "realtime":
        return {
            "type": "realtime_status",
            "vehicle": vehicle.get("numberPlate"),
            "status": derive_vehicle_status(vehicle),
            "last_updated": vehicle.get("lastUpdatedTime"),
            "TankerfuelCapacity": vehicle.get("TankerfuelCapacity"),
            "fuelCapacity": vehicle.get("fuelCapacity"),
            "battery_level": vehicle.get("batteryLevel")
        }

    return build_realtime_base(vehicle)



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


REALTIME_METRIC_MAP = {
    "speed": "speed",
    "weight": "Weight",
    "fuel_capacity": "fuelCapacity",
    "tanker_fuel_capacity": "TankerfuelCapacity",
    "battery": "batteryLevel"
}


def build_response(intent, api_result):

    # 🔥 ROUTE: REALTIME
    if intent.intent_type == "realtime":
        return build_realtime_response(intent, api_result)

    # 🔥 ROUTE: ALERTS (future-safe)
    # if intent.intent_type == "alert":
        # return build_alert_response(intent, api_result)

    # 🔥 DEFAULT: HISTORICAL
    rows = api_result.get("dataRows", [])
    summary = api_result.get("summary", {})

    if not rows:
        return {"error": "No data found"}

    plan = build_execution_plan(intent)

    # -----------------------------
    # CASE 1: METRIC QUERY
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
    # CASE 2: DETAILS QUERY
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