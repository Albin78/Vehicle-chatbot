from app.tools.vehicle_resolver import normalize_vehicle_id
from app.utils.value_cleaner import clean_value
from app.utils.response_utils import error_response
from app.utils.logger import logger


REALTIME_METRIC_MAP = {
    "speed": "speed",
    "weight": "Weight",
    "fuel_capacity": "fuelCapacity",
    "battery": "batteryLevel",
    "fuel_level": "fuelLevel",
    "mileage": "mileage",
    "seatbelt": "seatBelt",
    "door_open": "doorOpen",
    "imei": "IMEI",
    "vehicle_type": "typeName",
    "make": "makeName",
    "wasl": "WaslIdentityNumber",
    "fuel_consumed_today": "todayFuelConsumed",
    "seatbelt": "seatBelt",
    "tanker_fuel_capacity": "TankerfuelCapacity"
}


def filter_vehicle(records, vehicle_id):

    normalized = normalize_vehicle_id(vehicle_id)

    for record in records:

        plate = normalize_vehicle_id(
            record.get("numberPlate")
        )

        if plate == normalized:
            return record

    return None


def derive_vehicle_status(vehicle):

    vstatus_map = {
        1: "Moving",
        2: "Idle",
        3: "Stopped",
        4: "Disconnected"
    }

    vstatus = vehicle.get("vStatus")

    if vstatus in vstatus_map:
        return vstatus_map[vstatus]

    speed = float(vehicle.get("speed", 0) or 0)

    if speed > 0:
        return "Moving"

    return "Stopped"



def build_metric_response(vehicle, metrics):

    logger.info(
        f"Metrics input to realtime metric builder: {metrics}"
    )

    if not metrics:
        return error_response(
            "No realtime metrics requested"
        )

    metric_values = {}
    invalid_metrics = []

    for metric in metrics:

        metric = metric.lower()

        if metric not in REALTIME_METRIC_MAP:
            invalid_metrics.append(metric)
            continue

        field = REALTIME_METRIC_MAP[metric]

        value = vehicle.get(field)

        metric_values[metric] = value

    if not metric_values:

        return error_response(
            "No valid realtime metrics found"
        )

    return {

        "type": "realtime_metric",

        "vehicle": vehicle.get("numberPlate"),

        "metrics": metric_values,

        "invalid_metrics": invalid_metrics,

        "last_updated":
            vehicle.get("lastUpdatedTime")
    }



def build_status_response(vehicle):

    return {

        "type": "realtime_status",

        "vehicle": clean_value(
            vehicle.get("numberPlate")
        ),

        "status": derive_vehicle_status(vehicle),

        "speed": clean_value(
            vehicle.get("speed")
        ),

        "battery": clean_value(
            vehicle.get("batteryLevel")
        ),

        "fuel_level": clean_value(
            vehicle.get("fuelLevel")
        ),

        "fuel_capacity": clean_value(
            vehicle.get("fuelCapacity")
        ),

        "driver": clean_value(
            vehicle.get("driverName")
        ),

        "location": clean_value(
            vehicle.get("Location")
        ),

        "last_updated": clean_value(
            vehicle.get("lastUpdatedTime")
        ),

        "tankerfuelcapacity": clean_value(
            vehicle.get("TankerfuelCapacity")
        ),

        "fuelpercentage": clean_value(
            vehicle.get("fuelPercentage")
        ),

        "weight": clean_value(
            vehicle.get("Weight")
        ),

        "wasl": clean_value(
            vehicle.get("WaslIdentityNumber")
        ),

        "fuelconsumed_today": clean_value(
            vehicle.get("todayFuelConsumed")
        ),

        "imei": clean_value(
            vehicle.get("IMEI")
        ),

        "seatbelt": clean_value(
            vehicle.get("seatBelt")
        ),

        "door_status": clean_value(
            vehicle.get("doorOpen")
        ),

        "vehicle_type": clean_value(
            vehicle.get("typeName")
        ),

        "make": clean_value(
            vehicle.get("makeName")
        )
    }


def build_realtime_response(intent, api_result):

    records = api_result.get(
        "lastRecords",
        {}
    ).get(
        "data",
        []
    )

    if not records:
        return error_response(
            "No realtime records found"
        )

    vehicle = filter_vehicle(
        records,
        intent.vehicle_id
    )

    if not vehicle:
        return error_response(
            "Vehicle realtime data not found"
        )

    if intent.metrics:

        return build_metric_response(
            vehicle,
            intent.metrics
        )

    return build_status_response(vehicle)