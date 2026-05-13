from app.tools.vehicle_resolver import normalize_vehicle_id
from app.utils.response_utils import error_response


REALTIME_METRIC_MAP = {
    "speed": "speed",
    "weight": "Weight",
    "fuel_capacity": "fuelCapacity",
    "battery": "batteryLevel",
    "fuel_level": "fuelLevel",
    "mileage": "mileage",
    "SeatbeltAttacthDisplayValue": "Seatbelt",
    "doorOpen": "DoorOpen",
    "IMEI": "imei",
    "typeName": "type",
    "makeName": "Model",
    "WaslIdentityNumber": "Wasl",
    "todayFuelConsumed": "fuelconsumed_today"
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

    speed = vehicle.get("speed", 0)
    ignition = vehicle.get("ignitionOn", 0)

    if speed > 0:
        return "Moving"

    return "Stopped"



def build_metric_response(vehicle, metric):

    if metric not in REALTIME_METRIC_MAP:

        return error_response(
            f"Unsupported realtime metric: {metric}"
        )

    field = REALTIME_METRIC_MAP[metric]

    return {
        "vehicle": vehicle.get("numberPlate"),
        "metric": metric,
        "value": vehicle.get(field),
        "last_updated": vehicle.get("lastUpdated")
    }


def build_status_response(vehicle):

    return {

        "vehicle": vehicle.get("numberPlate"),

        "status": derive_vehicle_status(vehicle),

        "speed": vehicle.get("speed"),

        "battery": vehicle.get("batteryLevel"),

        "fuel_level": vehicle.get("fuelLevel"),

        "fuel_capacity": vehicle.get("fuelCapacity"),

        "driver": vehicle.get("driverName"),

        "location": vehicle.get("Location"),

        "last_updated": vehicle.get("lastUpdatedTime"),

        "tankerfuelcapacity": vehicle.get("TankerfuelCapacity"),

        "fuelpercentage": vehicle.get("fuelPercentage"),

        "weight": vehicle.get("Weight"),

        "Wasl": vehicle.get("WaslIdentityNumber"),

        "fuelconsumed_today": vehicle.get("todayFuelConsumed"),

        "imei": vehicle.get("IMEI")
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

    if intent.metric:
        return build_metric_response(
            vehicle,
            intent.metric
        )

    return build_status_response(vehicle)