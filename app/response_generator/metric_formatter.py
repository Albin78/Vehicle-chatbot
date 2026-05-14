import re

def clean_driver_name(driver: str | None) -> str | None:
    if not driver:
        return driver

    # Remove anything inside parentheses
    return re.sub(r"\s*\(.*?\)", "", driver).strip()

def get_unit(metric):
    unit_map = {
        "speed": "km/h",
        "distance": "km",
        "battery": "mV",
        "temperature": "°C"
    }
    return unit_map.get(metric, "")


def metric_not_available_response(metric: str, vehicle: str) -> str:
    suggestions = {
        "weight": "You can check speed, battery status, or fuel details instead.",
        "battery": "You can check speed or fuel details instead.",
        "speed": "You can check battery or fuel details instead.",
        "fuel_level": "You can check battery or fuel details instead."
    }

    suggestion_text = suggestions.get(metric, "Try asking for other vehicle details.")

    return (
        f"I couldn't find the current {metric} data for vehicle {vehicle}. "
        f"{suggestion_text}"
    )


def interpret_metric_value(metric, value):

    # -----------------------------------------
    # NULL / EMPTY
    # -----------------------------------------

    if value in [None, "", "NA", "null"]:
        return {
            "available": False,
            "text": (
                f"{metric.replace('_', ' ')} "
                f"data is currently unavailable"
            )
        }

    # -----------------------------------------
    # SEATBELT
    # -----------------------------------------

    if metric == "seatbelt":

        seatbelt_map = {
            0: "seatbelt is not fastened",
            1: "seatbelt is fastened"
        }

        return {
            "available": True,
            "text": seatbelt_map.get(
                int(value),
                f"seatbelt status is {value}"
            )
        }

    # -----------------------------------------
    # DOOR
    # -----------------------------------------

    if metric == "door_open":

        door_map = {
            0: "doors are closed",
            1: "doors are open"
        }

        return {
            "available": True,
            "text": door_map.get(
                int(value),
                f"door status is {value}"
            )
        }

    # -----------------------------------------
    # IGNITION
    # -----------------------------------------

    if metric == "ignition":

        ignition_map = {
            0: "ignition is off",
            1: "ignition is on"
        }

        return {
            "available": True,
            "text": ignition_map.get(
                int(value),
                f"ignition status is {value}"
            )
        }


    unit = get_unit(metric)

    readable_metric = metric.replace("_", " ")

    if unit:

        return {
            "available": True,
            "text": (
                f"{readable_metric} is "
                f"{value} {unit}"
            )
        }

    return {
        "available": True,
        "text": (
            f"{readable_metric} is {value}"
        )
    }