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
