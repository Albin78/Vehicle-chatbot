from app.response_generator.metric_formatter import (
    get_unit,
    clean_driver_name,
    interpret_metric_value
)

from app.utils.value_cleaner import has_value
from app.utils.logger import logger


# =========================================================
# SAFE VALUE
# =========================================================

def safe_value(value, suffix=""):

    if value in [None, "", "NA", "null"]:
        return None

    return f"{value}{suffix}"


# =========================================================
# REALTIME FORMATTER
# =========================================================

def format_realtime(result, intent):

    result_type = result.get("type")

    # =====================================================
    # REALTIME METRIC
    # =====================================================

    if result_type == "realtime_metric":

        vehicle = result.get("vehicle")

        metrics = result.get("metrics", {})

        invalid_metrics = result.get(
            "invalid_metrics",
            []
        )

        parts = []

        # ---------------------------------------------
        # VALID METRICS
        # ---------------------------------------------

        for metric, value in metrics.items():

            readable_metric = metric.replace(
                "_",
                " "
            )

            # -----------------------------------------
            # INTERPRET RAW API VALUE
            # -----------------------------------------

            interpreted_value = interpret_metric_value(
                metric,
                value
            )
            
            logger.info(f"Interpreted value: {interpreted_value}")
            if has_value(interpreted_value):

                unit = get_unit(metric)

                if unit:

                    parts.append(
                        f"{readable_metric} is "
                        f"{interpreted_value} {unit}"
                    )

                else:

                    parts.append(
                        f"{readable_metric} is "
                        f"{interpreted_value}"
                    )

            else:

                parts.append(
                    f"{readable_metric} data "
                    f"is currently unavailable"
                )

        # ---------------------------------------------
        # INVALID METRICS
        # ---------------------------------------------

        if invalid_metrics:

            invalid_text = ", ".join(
                invalid_metrics
            )

            parts.append(
                f"{invalid_text} "
                f"metric is not supported currently"
            )

        # ---------------------------------------------
        # LAST UPDATED
        # ---------------------------------------------

        if has_value(result.get("last_updated")):

            parts.append(
                f"last updated "
                f"{result.get('last_updated')}"
            )

        return (
            f"For vehicle {vehicle}, "
            + ". ".join(parts)
            + "."
        )

    # =====================================================
    # REALTIME STATUS
    # =====================================================

    if result_type == "realtime_status":

        parts = []

        vehicle = result.get("vehicle")

        status = result.get("status")

        parts.append(
            f"Vehicle {vehicle} "
            f"is currently {status}"
        )

        if has_value(result.get("speed")):

            parts.append(
                f"speed is "
                f"{result.get('speed')} km/h"
            )

        if has_value(result.get("battery")):

            parts.append(
                f"battery voltage is "
                f"{result.get('battery')} V"
            )

        else:

            parts.append(
                "battery data is currently unavailable"
            )

        if has_value(result.get("fuel_level")):

            parts.append(
                f"fuel level is "
                f"{result.get('fuel_level')}"
            )

        else:

            parts.append(
                "fuel level data is unavailable"
            )

        if has_value(result.get("fuel_capacity")):

            parts.append(
                f"fuel capacity is "
                f"{result.get('fuel_capacity')} L"
            )

        if has_value(
            result.get("tankerfuelcapacity")
        ):

            parts.append(
                f"tanker capacity is "
                f"{result.get('tankerfuelcapacity')} L"
            )

        if has_value(result.get("weight")):

            parts.append(
                f"vehicle weight is "
                f"{result.get('weight')} kg"
            )

        else:

            parts.append(
                "vehicle weight data is unavailable"
            )

        if has_value(result.get("seatbelt")):

            parts.append(
                f"seatbelt status is "
                f"{result.get('seatbelt')}"
            )

        else:

            parts.append(
                "seatbelt data is unavailable"
            )

        if has_value(result.get("door_open")):

            parts.append(
                f"door status is "
                f"{result.get('door_open')}"
            )

        else:

            parts.append(
                "door status data is unavailable"
            )

        if has_value(result.get("driver")):

            driver = clean_driver_name(
                result.get("driver")
            )

            parts.append(
                f"assigned driver is {driver}"
            )

        if has_value(result.get("wasl")):

            parts.append(
                f"vehicle Wasl registration is "
                f"{result.get('wasl')}"
            )

        if has_value(result.get("imei")):

            parts.append(
                f"IMEI is "
                f"{result.get('imei')}"
            )


        if has_value(result.get("vehicle_type")):

            parts.append(
                f"vehicle type is "
                f"{result.get('vehicle_type')}"
            )

        if has_value(result.get("make")):

            parts.append(
                f"manufacturer is "
                f"{result.get('make')}"
            )

        if has_value(result.get("last_updated")):

            parts.append(
                f"last updated "
                f"{result.get('last_updated')}"
            )

        return ". ".join(parts) + "."

    return "Realtime data unavailable."