from app.tools.vehicle_resolver import normalize_vehicle_id
from app.utils.value_cleaner import clean_value, safe_float
from app.utils.response_utils import error_response
from app.utils.logger import logger
from app.parsers.result_fomat_parser import (
    format_last_updated,
    build_location
)


# =========================================================
# REALTIME METRIC FIELD MAP
# =========================================================

REALTIME_METRIC_MAP = {

    "speed": "speed",

    "weight": "Weight",

    "fuel_capacity": "fuelCapacity",

    "fuel_level": "fuelLevel",

    "fuel_percentage": "fuelPercentage",

    "today_fuel_consumed": "todayFuelConsumed",

    "tanker_fuel_capacity": "TankerfuelCapacity",

    "tanker_fuel_percentage": "tankerFuelPercentage",

    "battery": "batteryLevel",

    "mileage": "mileage",

    "odometer_reading": "odometerCurrentReading",

    "seatbelt": "seatBelt",

    "door_open": "doorOpen",

    "imei": "IMEI",

    "vehicle_type": "typeName",

    "make": "makeName",

    "wasl": "WaslIdentityNumber",

    "ignition": "ignitionOn",

    "engine_status": "engineStatus",

    "engine_temperature": "engineTemperature",

    "engine_rpm": "engineRpm",

    "engine_hours": "engineHours",

    "driver_name": "driverName",

    "group_name": "groupName",

    "network": "networkType",

    "gsm_signal": "GSMSignal",

    "satellites": "satellites",

    "camera_status": "cameraStatus",

    "camera_imei": "CameraIMEI",

    "remote_immobilization": "RemoteImmobilaztion",

    "latitude": "lat",

    "longitude": "lon",

    "last_updated": "lastRecordAt",

    "model_name": "modelName",

    "tanker_status": "TankerEquipmentNumber"
}


# =========================================================
# FILTER VEHICLE
# =========================================================

def filter_vehicle(records, vehicle_id):

    normalized = normalize_vehicle_id(vehicle_id)

    for record in records:

        plate = normalize_vehicle_id(
            record.get("numberPlate")
        )

        if plate == normalized:
            return record

    return None


# =========================================================
# DERIVE VEHICLE STATUS
# =========================================================

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

    speed = safe_float(
        vehicle.get("speed")
    )

    if speed > 0:
        return "Moving"

    return "Stopped"


# =========================================================
# INTERPRET GSM SIGNAL
# =========================================================

def interpret_gsm_signal(vehicle) -> dict:

    gsm_val = vehicle.get("GSMSignal")
    if gsm_val is None:
        gsm_val = vehicle.get("gsmSignal")

    if gsm_val is None:
        return {"status": "no signal", "value": 0}

    try:
        gsm_int = int(float(gsm_val))
        if 3 <= gsm_int <= 5:
            return {"status": "good", "value": gsm_int}
        elif 0 < gsm_int < 3:
            return {"status": "bad", "value": gsm_int}
        elif gsm_int == 0:
            return {"status": "no signal", "value": 0}
        elif gsm_int > 5:
            return {"status": "good", "value": gsm_int}
        else:
            return {"status": "no signal", "value": gsm_int}
    except Exception:
        return {"status": "unknown", "value": gsm_val}


# =========================================================
# BUILD METRIC RESPONSE
# =========================================================

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

        # ---------------------------------------------
        # LOCATION SPECIAL CASE
        # ---------------------------------------------

        if metric == "location":

            metric_values["location"] = build_location(
                vehicle.get("lat"),
                vehicle.get("lon")
            )

            continue

        if metric not in REALTIME_METRIC_MAP:

            invalid_metrics.append(metric)

            continue

        # =====================================================
        # GSM SIGNAL
        # =====================================================

        if metric == "gsm_signal":

            metric_values[metric] = interpret_gsm_signal(vehicle)

            continue

        # =====================================================
        # TANKER STATUS
        # =====================================================

        if metric == "tanker_status":

            tanker_val = vehicle.get("TankerEquipmentNumber")

            is_tanker = False
            if tanker_val is not None:
                val_str = str(tanker_val).strip().upper()
                if val_str not in ["", "NULL", "NONE", "NA", "N/A", "-", "--", "UNKNOWN"]:
                    is_tanker = True

            metric_values[metric] = "tanker" if is_tanker else "can"

            continue

        # =====================================================
        # CAMERA STATUS
        # =====================================================

        if metric == "camera_status":

            metric_values[metric] = {

                "status":
                    vehicle.get("CameraStatus"),

                "channels":
                    vehicle.get("CameraChannel")
            }

            continue


        # =====================================================
        # NORMAL FIELDS
        # =====================================================

        field = REALTIME_METRIC_MAP[metric]

        value = vehicle.get(field)

        metric_values[metric] = value

        # ---------------------------------------------
        # FORMAT LAST UPDATED
        # ---------------------------------------------

        if metric == "last_updated":

            value = format_last_updated(value)

        metric_values[metric] = clean_value(value)

    if not metric_values:

        return error_response(
            "No valid realtime metrics found"
        )

    return {

        "type": "realtime_metric",

        "vehicle": clean_value(
            vehicle.get("numberPlate")
        ),

        "metrics": metric_values,

        "invalid_metrics": invalid_metrics,

        "last_updated": format_last_updated(
            vehicle.get("lastRecordAt")
        )
    }


# =========================================================
# BUILD STATUS RESPONSE
# =========================================================

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

        "fuel_percentage": clean_value(
            vehicle.get("fuelPercentage")
        ),

        "today_fuel_consumed": clean_value(
            vehicle.get("todayFuelConsumed")
        ),

        "tanker_fuel_capacity": clean_value(
            vehicle.get("TankerfuelCapacity")
        ),

        "tanker_fuel_percentage": clean_value(
            vehicle.get("tankerFuelPercentage")
        ),

        "driver_name": clean_value(
            vehicle.get("driverName")
        ),

        "group_name": clean_value(
            vehicle.get("groupName")
        ),

        # ---------------------------------------------
        # LOCATION OBJECT
        # ---------------------------------------------

        "location": build_location(
            vehicle.get("lat"),
            vehicle.get("lon")
        ),

        "weight": clean_value(
            vehicle.get("Weight")
        ),

        "mileage": clean_value(
            vehicle.get("mileage")
        ),

        "odometer_reading": clean_value(
            vehicle.get("odometerCurrentReading")
        ),

        "wasl": clean_value(
            vehicle.get("WaslIdentityNumber")
        ),

        "imei": clean_value(
            vehicle.get("IMEI")
        ),

        "seatbelt": clean_value(
            vehicle.get("seatBelt")
        ),

        "door_open": clean_value(
            vehicle.get("doorOpen")
        ),

        "vehicle_type": clean_value(
            vehicle.get("typeName")
        ),

        "make": clean_value(
            vehicle.get("makeName")
        ),

        "model_name": clean_value(
            vehicle.get("modelName")
        ),

        "tanker_status": (
            "tanker" if (
                vehicle.get("TankerEquipmentNumber") is not None
                and str(vehicle.get("TankerEquipmentNumber")).strip().upper() not in ["", "NULL", "NONE", "NA", "N/A", "-", "--", "UNKNOWN"]
            ) else "can"
        ),

        "ignition": clean_value(
            vehicle.get("ignitionOn")
        ),

        "engine_status": clean_value(
            vehicle.get("engineStatus")
        ),

        "engine_temperature": clean_value(
            vehicle.get("engineTemperature")
        ),

        "engine_rpm": clean_value(
            vehicle.get("engineRpm")
        ),

        "engine_hours": clean_value(
            vehicle.get("engineHours")
        ),

        "gsm_signal": interpret_gsm_signal(vehicle),

        "network": clean_value(
            vehicle.get("networkType")
        ),

        "satellites": clean_value(
            vehicle.get("satellites")
        ),

        "camera_status": {
            "status": vehicle.get("CameraStatus"),
            "channels": vehicle.get("CameraChannel")
        },

        "camera_imei": clean_value(
            vehicle.get("CameraIMEI")
        ),

        "remote_immobilization": clean_value(
            vehicle.get("RemoteImmobilaztion")
        ),

        "last_updated": format_last_updated(
            vehicle.get("lastRecordAt")
        )
    }


# =========================================================
# MAIN RESPONSE BUILDER
# =========================================================

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