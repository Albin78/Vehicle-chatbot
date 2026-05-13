from app.response_generator.metric_formatter import (
    get_unit,
    clean_driver_name,
    metric_not_available_response
)


def format_realtime(result, intent):

    result_type = result.get("type")

    if result_type == "realtime_metric":

        metric = result.get("metric")
        value = result.get("value")

        if value is None:
            return metric_not_available_response(
                metric,
                result.get("vehicle")
            )

        unit = get_unit(metric)

        return (
            f"The current {metric} of vehicle "
            f"{result.get('vehicle')} is "
            f"{value} {unit}."
        )

    if result_type == "realtime_status":

        parts = []

        parts.append(
            f"Vehicle {result.get('vehicle')} "
            f"is currently {result.get('status')}"
        )

        if result.get("speed") is not None:
            parts.append(
                f"moving at {result.get('speed')} km/h"
            )

        if result.get("battery_level"):
            parts.append(
                f"battery level is "
                f"{result.get('battery_level')} V"
            )

        if result.get("fuel_capacity"):
            parts.append(
                f"fuel capacity is "
                f"{result.get('fuel_capacity')} L"
            )

        if result.get("weight") is not None:
            parts.append(
                f"weight is {result.get('weight')} kg"
            )

        if result.get("driver"):
            driver = clean_driver_name(
                result.get("driver")
            )

            parts.append(
                f"assigned driver is {driver}"
            )

        return ". ".join(parts) + "."