import re
from typing import Any


# =========================================================
# DRIVER NAME CLEANER
# =========================================================

def clean_driver_name(driver: str | None) -> str | None:

    if not driver:
        return None

    return re.sub(
        r"\s*\(.*?\)",
        "",
        driver
    ).strip()


# =========================================================
# UNIT MAP
# =========================================================

def get_unit(metric: str) -> str:

    unit_map = {

        "speed": "km/h",

        "distance": "km",

        "distance_travelled": "km",

        "mileage": "km/L",

        "battery": "V",

        "engine_temperature": "°C",

        "fuel_capacity": "L",

        "fuel_level": "L",

        "today_fuel_consumed": "L",

        "tanker_fuel_capacity": "L",

        "weight": "kg"
    }

    return unit_map.get(metric, "")


# =========================================================
# INVALID VALUE CHECK
# =========================================================

def is_invalid_value(value: Any) -> bool:

    invalid_values = {
        None,
        "",
        " ",
        "NA",
        "N/A",
        "NULL",
        "NONE",
        "UNKNOWN",
        "-",
        "--"
    }

    # Dicts are considered valid (could be location, camera_status, etc.)
    if isinstance(value, dict):
        return False

    if isinstance(value, str):

        value = value.strip().upper()

    return value in invalid_values


# =========================================================
# GENERIC UNAVAILABLE RESPONSE
# =========================================================

def unavailable_response(metric: str):

    readable_metric = metric.replace(
        "_",
        " "
    )

    return {
        "available": False,
        "text":
            f"{readable_metric} data is unavailable"
    }


# =========================================================
# MAIN METRIC INTERPRETER
# =========================================================

def interpret_metric_value(
    metric: str,
    value: Any
):

    # =====================================================
    # INVALID / EMPTY
    # =====================================================

    if is_invalid_value(value):

        return unavailable_response(metric)

    readable_metric = metric.replace(
        "_",
        " "
    )

    # =====================================================
    # LOCATION
    # =====================================================

    if metric == "location":

        if not isinstance(value, dict):

            return unavailable_response(metric)

        # latitude = value.get("latitude")

        # longitude = value.get("longitude")

        map_url = value.get("google_maps_url")

        # ---------------------------------------------
        # MAP URL PRIORITY
        # ---------------------------------------------

        if map_url:

            return {
                "available": True,
                "text":
                    f"current location: {map_url}"
            }

        # ---------------------------------------------
        # COORDINATES FALLBACK
        # ---------------------------------------------

        # if latitude is not None and longitude is not None:

        #     return {
        #         "available": True,
        #         "text":
        #             (
        #                 "current location coordinates "
        #                 f"are {latitude}, {longitude}"
        #             )
        #     }

        return unavailable_response(metric)

    # =====================================================
    # SEATBELT
    # =====================================================

    if metric == "seatbelt":

        try:

            seatbelt_value = int(value)

        except Exception:

            return unavailable_response(metric)

        if seatbelt_value == 0:

            return {
                "available": True,
                "text":
                    (
                        "seatbelt is equipped but not fastened "
                        
                    )
            }

        if seatbelt_value == 1:

            return {
                "available": True,
                "text":
                    (
                        "seatbelt is equipped but is fastened "
                    )
            }

        return {
            "available": True,
            "text":
                "seat is not equipped"
        }

    # =====================================================
    # DOOR STATUS
    # =====================================================

    if metric == "door_open":

        try:

            door_value = int(value)

        except Exception:

            return unavailable_response(metric)

        door_map = {

            0: "doors are closed",

            1: "doors are open"
        }

        return {
            "available": True,
            "text":
                door_map.get(
                    door_value,
                    f"door status is {value}"
                )
        }

    # =====================================================
    # IGNITION
    # =====================================================

    if metric == "ignition":

        try:

            ignition_value = int(value)

        except Exception:

            return unavailable_response(metric)

        ignition_map = {

            0: "ignition is off",

            1: "ignition is on"
        }

        return {
            "available": True,
            "text":
                ignition_map.get(
                    ignition_value,
                    f"ignition status is {value}"
                )
        }

    # =====================================================
    # REMOTE IMMOBILIZATION
    # =====================================================

    if metric == "remote_immobilization":

        try:

            remote_value = int(value)

        except Exception:

            return unavailable_response(metric)

        # ---------------------------------------------
        # FEATURE EXISTS IF VALUE EXISTS
        # ---------------------------------------------

        if remote_value == 0:

            return {
                "available": True,
                "text":
                    (
                        "vehicle supports remote "
                        "immobilization and is currently "
                        "not remotely immobilized"
                    )
            }

        if remote_value == 1:

            return {
                "available": True,
                "text":
                    (
                        "vehicle supports remote "
                        "immobilization and is currently "
                        "remotely immobilized"
                    )
            }

        return {
            "available": True,
            "text":
                "vehicle supports remote immobilization"
        }

    # =====================================================
    # CAMERA STATUS
    # =====================================================

    if metric == "camera_status":

        # ---------------------------------------------
        # SIMPLE INTEGER / STRING STATUS
        # ---------------------------------------------

        if isinstance(value, (int, str)):

            try:

                status = int(value)

            except Exception:

                status = None

            if status == 0:

                return {
                    "available": True,
                    "text":
                        "camera is not equipped"
                }

            if status == 1:

                return {
                    "available": True,
                    "text":
                        "camera is equipped"
                }

        # ---------------------------------------------
        # STRUCTURED CAMERA OBJECT
        # ---------------------------------------------

        if isinstance(value, dict):

            status = value.get("status")

            channels = value.get("channels")

            # -----------------------------------------
            # NOT EQUIPPED
            # -----------------------------------------

            if status in [0, "0", False]:

                return {
                    "available": True,
                    "text":
                        "camera is not equipped"
                }

            # -----------------------------------------
            # EQUIPPED
            # -----------------------------------------

            if status in [1, "1", True]:

                # -------------------------------------
                # LIST CHANNELS
                # -------------------------------------

                if isinstance(channels, list):

                    valid_channels = [

                        ch for ch in channels

                        if ch is not None
                    ]

                    count = len(valid_channels)

                    if count == 0:

                        return {
                            "available": True,
                            "text":
                                "camera is equipped"
                        }

                    if count == 1:

                        return {
                            "available": True,
                            "text":
                                (
                                    "camera is equipped "
                                    "with 1 camera channel"
                                )
                        }

                    return {
                        "available": True,
                        "text":
                            (
                                "camera is equipped "
                                f"with {count} camera channels"
                            )
                    }

                # -------------------------------------
                # INTEGER / DIGIT STRING
                # -------------------------------------

                if str(channels).isdigit() and channels:

                    count = int(channels)

                    if count == 1:

                        return {
                            "available": True,
                            "text":
                                (
                                    "camera is equipped "
                                    "with 1 camera channel"
                                )
                        }

                    return {
                        "available": True,
                        "text":
                            (
                                "camera is equipped "
                                f"with {count} camera channels"
                            )
                    }

                return {
                    "available": True,
                    "text":
                        "camera is equipped"
                }

        return unavailable_response(metric)

    # =====================================================
    # DRIVER NAME
    # =====================================================

    if metric == "driver_name":

        cleaned_driver = clean_driver_name(
            str(value)
        )

        if not cleaned_driver:

            return unavailable_response(metric)

        return {
            "available": True,
            "text":
                f"driver assigned is {cleaned_driver}"
        }

    # =====================================================
    # VEHICLE STATUS
    # =====================================================

    if metric == "status":

        return {
            "available": True,
            "text":
                f"vehicle status is {value}"
        }

    # =====================================================
    # MAKE
    # =====================================================

    if metric == "make":

        return {
            "available": True,
            "text":
                f"manufacturer is {value}"
        }

    # =====================================================
    # VEHICLE TYPE
    # =====================================================

    if metric == "vehicle_type":

        return {
            "available": True,
            "text":
                f"vehicle type is {value}"
        }

    # =====================================================
    # IMEI
    # =====================================================

    if metric == "imei":

        return {
            "available": True,
            "text":
                f"IMEI is {value}"
        }

    # =====================================================
    # LAST UPDATED
    # =====================================================

    if metric == "last_updated":

        return {
            "available": True,
            "text":
                f"last updated {value}"
        }

    # =====================================================
    # SATELLITES
    # OPTIONAL / LOW PRIORITY
    # =====================================================

    # if metric == "satellites":

    #     return {
    #         "available": True,
    #         "text":
    #             f"{value} satellites connected"
    #     }

    # =====================================================
    # GENERIC UNIT-BASED METRICS
    # =====================================================

    unit = get_unit(metric)

    if unit:

        return {
            "available": True,
            "text":
                f"{readable_metric} is {value} {unit}"
        }

    # =====================================================
    # GENERIC FALLBACK
    # =====================================================

    return {
        "available": True,
        "text":
            f"{readable_metric} is {value}"
    }