from app.utils.logger import logger


# =========================================================
# HUMAN-READABLE ALERT NAMES
# =========================================================

ALERT_DISPLAY_NAMES = {
    "overSpeed":            "Overspeed",
    "idling":               "Idling",
    "overStay":             "Overstay",
    "batteryDisconnection": "Battery Disconnection",
    "lowBattery":           "Low Battery",
    "rashDriving":          "Rash Driving",
    "continuous":           "Continuous Driving",
    "territory":            "Territory / Geofence",
    "refuelDrain":          "Refuel Drain",
    "fuelDisconnection":    "Fuel Disconnection",
    "parkfence":            "Park Fence",
    "overload":             "Overload",
    "WeightTamper":         "Weight Tamper",
    "Accident":             "Accident",
    "seatbelt":             "Seatbelt",
    "assetmovement":        "Asset Movement",
    "territoryOverSpeed":   "Territory Overspeed",
    "safeStopFuelDrainer":  "Safe Stop Fuel Drainer",
    "equipmentByPass":      "Equipment Bypass",
    "afterhoursmovement":   "After-Hours Movement",
    "zoneBasedSpeedLimit":  "Zone-Based Speed Limit",
}

# Fields in the values dict that are NOT boolean enable/disable flags
NON_FLAG_FIELDS = {
    "overspeedStartTime",
    "overSpeedAlertID",
    "overSpeedMax",
    "overSpeedTime",
    "idlingStartTime",
    "idlingTime",
}


# =========================================================
# SINGLE ALERT TYPE RESPONSE
# =========================================================

def build_alert_enable_single_response(
    intent,
    record,
    alert_type_focus: str
):
    """
    Returns a structured response for a specific alert type query,
    e.g. "Is overspeed alert enabled on vehicle 1832RXB?"
    """

    values = record.get("values", {})

    flag_value = values.get(alert_type_focus)
    logger.info(f"Flag value [ALERT Enable Builder]: {flag_value}")

    display_name = ALERT_DISPLAY_NAMES.get(
        alert_type_focus,
        alert_type_focus.replace("_", " ").title()
    )

    if flag_value is None:

        return {
            "type": "alert_enable_single",
            "vehicle": intent.vehicle_id,
            "alert_type": alert_type_focus,
            "alert_display_name": display_name,
            "enabled": None,
            "status_text": "unknown",
        }

    enabled = bool(flag_value)

    return {
        "type": "alert_enable_single",
        "vehicle": intent.vehicle_id,
        "alert_type": alert_type_focus,
        "alert_display_name": display_name,
        "enabled": enabled,
        "status_text": "enabled" if enabled else "disabled",
    }


# =========================================================
# ALL ALERTS OVERVIEW RESPONSE
# =========================================================

def build_alert_enable_all_response(
    intent,
    record
):
    """
    Returns a full breakdown of enabled/disabled alerts for the vehicle.
    """

    values = record.get("values", {})

    enabled_alerts = []
    disabled_alerts = []

    for key, val in values.items():

        if key in NON_FLAG_FIELDS:
            continue

        if not isinstance(val, bool):
            continue

        display = ALERT_DISPLAY_NAMES.get(
            key,
            key.replace("_", " ").title()
        )

        if val:
            enabled_alerts.append(display)

        else:
            disabled_alerts.append(display)

    return {
        "type": "alert_enable_all",
        "vehicle": intent.vehicle_id,
        "enabled_alerts": enabled_alerts,
        "disabled_alerts": disabled_alerts,
        "enabled_count": len(enabled_alerts),
        "disabled_count": len(disabled_alerts),
    }


# =========================================================
# MAIN ROUTER
# =========================================================

def build_alert_enable_response(intent, record):

    alert_type_focus = getattr(intent, "alert_type_focus", None)

    logger.info(
        f"[ALERT ENABLE BUILDER] "
        f"alert_type_focus={alert_type_focus}, "
        f"vehicle={intent.vehicle_id}"
    )

    # ---------------------------------------------------
    # FOCUSED: specific alert type asked
    # ---------------------------------------------------

    if alert_type_focus:

        return build_alert_enable_single_response(
            intent=intent,
            record=record,
            alert_type_focus=alert_type_focus
        )

    # ---------------------------------------------------
    # GENERAL: all alerts for the vehicle
    # ---------------------------------------------------

    return build_alert_enable_all_response(
        intent=intent,
        record=record
    )
