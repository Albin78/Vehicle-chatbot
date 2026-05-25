from app.utils.logger import logger


# =========================================================
# SINGLE ALERT TYPE FORMATTER
# =========================================================

def format_alert_enable_single(result, intent):
    """
    Formats: "Is overspeed alert enabled on vehicle 1832RXB?"
    Output:  "For vehicle 1832RXB, the Overspeed alert is enabled."
    """

    vehicle = result.get("vehicle", intent.vehicle_id)
    display_name = result.get("alert_display_name", "alert")
    enabled = result.get("enabled")
    status_text = result.get("status_text", "unknown")

    if enabled is None:

        return (
            f"For vehicle {vehicle}, "
            f"the {display_name} alert configuration is unknown."
        )

    return (
        f"For vehicle {vehicle}, "
        f"the {display_name} alert is {status_text}."
    )


# =========================================================
# ALL ALERTS FORMATTER
# =========================================================

def format_alert_enable_all(result, intent):
    """
    Formats a complete list of enabled and disabled alerts for a vehicle.
    """

    vehicle = result.get("vehicle", intent.vehicle_id)
    enabled_alerts = result.get("enabled_alerts", [])
    disabled_alerts = result.get("disabled_alerts", [])
    enabled_count = result.get("enabled_count", 0)
    disabled_count = result.get("disabled_count", 0)

    parts = []

    parts.append(
        f"For vehicle {vehicle}, "
        f"{enabled_count} alert(s) are enabled "
        f"and {disabled_count} are disabled"
    )

    if enabled_alerts:

        enabled_list = ", ".join(enabled_alerts)
        parts.append(
            f"Enabled alerts: {enabled_list}"
        )

    if disabled_alerts:

        disabled_list = ", ".join(disabled_alerts)
        parts.append(
            f"Disabled alerts: {disabled_list}"
        )

    return ". ".join(parts) + "."


# =========================================================
# MAIN FORMATTER ROUTER
# =========================================================

def format_alert_enable(result, intent):

    result_type = result.get("type")

    logger.info(f"[ALERT ENABLE FORMATTER] type={result_type}")

    if result_type == "error":

        return result.get(
            "message",
            "Unable to fetch alert configuration."
        )

    if result_type == "alert_enable_single":

        return format_alert_enable_single(result, intent)

    if result_type == "alert_enable_all":

        return format_alert_enable_all(result, intent)

    return "Unable to format alert enable response."
