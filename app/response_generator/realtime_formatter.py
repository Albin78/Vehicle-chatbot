from app.response_generator.metric_formatter import (
    clean_driver_name,
    interpret_metric_value
)

from app.utils.value_cleaner import (
    has_value
)


# =========================================================
# LOCATION
# =========================================================

def format_location(location_data):

    if not isinstance(location_data, dict):
        return None

    google_maps = location_data.get(
        "google_maps_url"
    )

    if not has_value(google_maps):
        return None

    return f"Location map: {google_maps}"


# =========================================================
# FIELD FORMATTERS
# =========================================================

FIELD_FORMATTERS = {

    # -----------------------------------------------------
    # SPEED
    # -----------------------------------------------------

    "speed":
        lambda v:
            f"Speed is {v} km/h",

    # -----------------------------------------------------
    # BATTERY
    # -----------------------------------------------------

    "battery":
        lambda v:
            f"Battery voltage is {v} V",

    # -----------------------------------------------------
    # FUEL
    # -----------------------------------------------------

    "fuel_level":
        lambda v:
            f"Fuel level is {v} L",

    "fuel_percentage":
        lambda v:
            f"Fuel level is {v}%",

    "fuel_capacity":
        lambda v:
            f"Fuel capacity is {v} L",

    "today_fuel_consumed":
        lambda v:
            f"Today's fuel consumed is {v} L",

    "tanker_fuel_capacity":
        lambda v:
            f"Tanker fuel capacity is {v} L",

    "tanker_fuel_percentage":
        lambda v:
            f"Tanker fuel level is {v}%",

    # -----------------------------------------------------
    # DRIVER / GROUP
    # -----------------------------------------------------

    "driver_name":
        lambda v:
            f"Driver assigned is "
            f"{clean_driver_name(v)}",

    "group_name":
        lambda v:
            f"Vehicle group is {v}",

    # -----------------------------------------------------
    # VEHICLE INFO
    # -----------------------------------------------------

    "vehicle_type":
        lambda v:
            f"Vehicle type is {v}",

    "make":
        lambda v:
            f"Manufacturer is {v}",

    "imei":
        lambda v:
            f"IMEI is {v}",

    "wasl":
        lambda v:
            f"WASL identity number is {v}",

    # -----------------------------------------------------
    # OPERATIONAL
    # -----------------------------------------------------

    "weight":
        lambda v:
            f"Weight is {v}",

    "mileage":
        lambda v:
            f"Mileage is {v}",

    "odometer_reading":
        lambda v:
            f"Odometer reading is {v} km",

    # -----------------------------------------------------
    # ENGINE
    # -----------------------------------------------------

    "engine_status":
        lambda v:
            f"Engine status is {v}",

    "engine_temperature":
        lambda v:
            f"Engine temperature is {v} °C",

    "engine_rpm":
        lambda v:
            f"Engine RPM is {v}",

    "engine_hours":
        lambda v:
            f"Engine hours are {v}",

    # -----------------------------------------------------
    # CONNECTIVITY
    # -----------------------------------------------------

    "gsm_signal":
        lambda v:
            f"GSM signal is {v}",

    "network":
        lambda v:
            f"Network type is {v}",
}


# =========================================================
# SUMMARY FIELD ORDER
# =========================================================

SUMMARY_FIELDS = [

    # Fuel
    "fuel_level",
    "fuel_percentage",
    "fuel_capacity",
    "today_fuel_consumed",
    "tanker_fuel_capacity",
    "tanker_fuel_percentage",

    # Electrical
    "battery",

    # Identity
    "imei",
    "vehicle_type",
    "make",
    "group_name",
    "driver_name",

    # Vehicle state
    "ignition",
    "seatbelt",
    "door_open",
    "camera_status",
    "remote_immobilization",

    # Engine
    "engine_status",
    "engine_temperature",
    "engine_rpm",
    "engine_hours",

    # Operational
    "weight",
    "mileage",
    "odometer_reading",

    # Connectivity
    "network",
    "gsm_signal",

    # Compliance
    "wasl",
]


# =========================================================
# SPECIAL METRICS
# =========================================================

SPECIAL_METRICS = {

    "ignition",
    "seatbelt",
    "door_open",
    "camera_status",
    "remote_immobilization",
    "location",
}


# =========================================================
# FORMAT METRIC
# =========================================================

def format_metric(metric, value):

    # -----------------------------------------------------
    # EMPTY / INVALID
    # -----------------------------------------------------

    if not has_value(value):
        return None

    # -----------------------------------------------------
    # SPECIAL METRICS
    # -----------------------------------------------------

    if metric in SPECIAL_METRICS:

        interpreted = interpret_metric_value(
            metric,
            value
        )

        if (
            interpreted
            and interpreted.get("available")
            and interpreted.get("text")
        ):

            return interpreted["text"]

        return None

    # -----------------------------------------------------
    # STANDARD FORMATTERS
    # -----------------------------------------------------

    formatter = FIELD_FORMATTERS.get(metric)

    if formatter:

        try:
            return formatter(value)

        except Exception:
            return None

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    readable_metric = metric.replace(
        "_",
        " "
    ).capitalize()

    return f"{readable_metric} is {value}"


# =========================================================
# REALTIME METRIC FORMATTER
# =========================================================

# =========================================================
# REALTIME METRIC FORMATTER
# =========================================================

def format_realtime_metric(result):

    vehicle = result.get("vehicle")

    metrics = result.get(
        "metrics",
        {}
    )

    parts = []

    unavailable_metrics = []

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    for metric, value in metrics.items():

        formatted = format_metric(
            metric,
            value
        )

        # -------------------------------------------------
        # VALID METRIC
        # -------------------------------------------------

        if formatted:

            parts.append(formatted)

        # -------------------------------------------------
        # UNAVAILABLE METRIC
        # -------------------------------------------------

        else:

            readable_metric = (
                metric.replace("_", " ")
            )

            unavailable_metrics.append(
                readable_metric
            )

    # -----------------------------------------------------
    # NO VALID METRICS
    # -----------------------------------------------------

    if not parts:

        # -------------------------------------------------
        # SINGLE UNAVAILABLE
        # -------------------------------------------------

        if len(unavailable_metrics) == 1:

            metric_name = (
                unavailable_metrics[0]
                .capitalize()
            )

            return (
                f"{metric_name} data is currently "
                f"unavailable for vehicle "
                f"{vehicle}."
            )

        # -------------------------------------------------
        # MULTIPLE UNAVAILABLE
        # -------------------------------------------------

        if unavailable_metrics:

            metrics_text = ", ".join(
                unavailable_metrics
            )

            return (
                f"The following realtime metrics "
                f"are currently unavailable for "
                f"vehicle {vehicle}: "
                f"{metrics_text}."
            )

        # -------------------------------------------------
        # EMPTY
        # -------------------------------------------------

        return (
            f"No realtime telemetry data "
            f"is currently available "
            f"for vehicle {vehicle}."
        )

    # -----------------------------------------------------
    # LAST UPDATED
    # ONLY IF VALID METRICS EXIST
    # -----------------------------------------------------

    last_updated = result.get(
        "last_updated"
    )

    if has_value(last_updated):

        parts.append(
            f"Last updated {last_updated}"
        )

    # -----------------------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------------------

    return (
        f"For vehicle {vehicle}, "
        + ". ".join(parts)
        + "."
    )

# =========================================================
# REALTIME STATUS FORMATTER
# =========================================================

def format_realtime_status(result):

    vehicle = result.get("vehicle")

    parts = []

    # -----------------------------------------------------
    # STATUS + SPEED
    # -----------------------------------------------------

    status = result.get("status")

    speed = result.get("speed")

    if has_value(status):

        if (
            str(status).lower() == "moving"
            and has_value(speed)
        ):

            parts.append(
                f"Vehicle {vehicle} is currently "
                f"moving at {speed} km/h"
            )

        else:

            parts.append(
                f"Vehicle {vehicle} status is {status}"
            )

    # -----------------------------------------------------
    # SUMMARY METRICS
    # -----------------------------------------------------

    for field in SUMMARY_FIELDS:

        formatted = format_metric(
            field,
            result.get(field)
        )

        if formatted:
            parts.append(formatted)

    # -----------------------------------------------------
    # LOCATION
    # -----------------------------------------------------

    location_text = format_location(
        result.get("location")
    )

    if location_text:
        parts.append(location_text)

    # -----------------------------------------------------
    # LAST UPDATED
    # -----------------------------------------------------

    last_updated = result.get(
        "last_updated"
    )

    if has_value(last_updated):

        parts.append(
            f"Last updated {last_updated}"
        )

    # -----------------------------------------------------
    # EMPTY RESPONSE
    # -----------------------------------------------------

    if not parts:

        return (
            f"No realtime status data "
            f"is currently available "
            f"for vehicle {vehicle}"
        )

    # -----------------------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------------------

    return ". ".join(parts) + "."


# =========================================================
# MAIN FORMATTER ENTRY
# =========================================================

def format_realtime(result, intent):

    result_type = result.get("type")

    # -----------------------------------------------------
    # REALTIME METRIC RESPONSE
    # -----------------------------------------------------

    if result_type == "realtime_metric":

        return format_realtime_metric(
            result
        )

    # -----------------------------------------------------
    # REALTIME STATUS RESPONSE
    # -----------------------------------------------------

    if result_type == "realtime_status":

        return format_realtime_status(
            result
        )

    # -----------------------------------------------------
    # UNKNOWN
    # -----------------------------------------------------

    return "Realtime data unavailable."