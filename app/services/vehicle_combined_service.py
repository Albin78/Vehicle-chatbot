from app.tools.vehicle_resolver import resolve_vehicle

from app.tools.external_api_tool import combined_report

from app.builders.api_payload_builder import (
    build_combined_payload
)

from app.validators.result_validator import (
    validate_api_response
)

from app.builders.response_route import (
    build_response
)

from app.utils.logger import logger


def handle_vehicle_service(
    intent,
    plan,
    company_id
):

    # --------------------------------------------------
    # RESOLVE VEHICLE
    # --------------------------------------------------

    vehicle = resolve_vehicle(
        plan.vehicle_id,
        company_id
    )

    if not vehicle:

        return {
            "type": "error",
            "message": "Vehicle not found"
        }

    logger.info(f"[SERVICE] Vehicle: {vehicle}")

    # --------------------------------------------------
    # PRE-CHECK: ALERT ENABLEMENT CHECK FOR FOCUSED ALERTS
    # --------------------------------------------------
    if intent.source == "alert" and getattr(intent, "alert_focus", None):
        alert_focus_raw = intent.alert_focus.lower().replace("_", "").replace("-", "")
        
        # Let's map alert_focus_raw to canonical key
        MAPPING = {
            "overspeed": "overSpeed",
            "idling": "idling",
            "overstay": "overStay",
            "battery_disconnection": "batteryDisconnection",
            "battery_disconnect": "batteryDisconnection",
            "low_battery": "lowBattery",
            "rash_driving": "rashDriving",
            "harsh_driving": "rashDriving",
            "continuous": "continuous",
            "continuous_driving": "continuous",
            "territory": "territory",
            "geofence": "territory",
            "refuel_drain": "refuelDrain",
            "fuel_disconnection": "fuelDisconnection",
            "parkfence": "parkfence",
            "park_fence": "parkfence",
            "overload": "overload",
            "weight_tamper": "WeightTamper",
            "accident": "Accident",
            "seatbelt": "seatbelt",
            "asset_movement": "assetmovement",
            "assetmovement": "assetmovement",
            "territory_overspeed": "territoryOverSpeed",
            "territoryoverspeed": "territoryOverSpeed",
            "safe_stop_fuel_drainer": "safeStopFuelDrainer",
            "equipment_bypass": "equipmentByPass",
            "afterhoursmovement": "afterhoursmovement",
            "afterhours_movement": "afterhoursmovement",
            "afterhours": "afterhoursmovement",
            "after_hours": "afterhoursmovement",
            "zone_based_speed_limit": "zoneBasedSpeedLimit",
        }
        
        alert_flag_key = None
        for k, v in MAPPING.items():
            k_clean = k.lower().replace("_", "").replace("-", "")
            if alert_focus_raw == k_clean or alert_focus_raw in k_clean:
                alert_flag_key = v
                break
        
        if alert_flag_key:
            from app.tools.external_api_tool import get_alert_enable_status
            from app.builders.alert_enable_builder import ALERT_DISPLAY_NAMES
            
            logger.info(f"[SERVICE] Checking enablement status for {alert_flag_key} on vehicle {intent.vehicle_id}")
            api_result = get_alert_enable_status(company_id=company_id)
            if isinstance(api_result, dict) and not api_result.get("response"):
                data_list = api_result.get("data", [])
                if isinstance(data_list, list):
                    matched_record = None
                    vehicle_numeric_id = vehicle.get("ID")
                    for record in data_list:
                        if isinstance(record, dict):
                            record_id = record.get("ID")
                            if record_id and str(record_id) == str(vehicle_numeric_id):
                                matched_record = record
                                break
                    
                    if matched_record:
                        values = matched_record.get("values", {})
                        if isinstance(values, dict):
                            flag_value = values.get(alert_flag_key)
                            logger.info(f"[SERVICE] Enablement status value for {alert_flag_key}: {flag_value}")
                            if flag_value is False:
                                display_name = ALERT_DISPLAY_NAMES.get(alert_flag_key, alert_flag_key)
                                return {
                                    "error": f"{display_name} alerts are currently disabled in the configuration for vehicle {intent.vehicle_id}. Please enable it in the policy settings to track this metric."
                                }

    # --------------------------------------------------
    # BUILD PAYLOAD WITH DYNAMIC DATE BACKOFF FOR ALERTS
    # --------------------------------------------------

    from datetime import datetime, timezone, timedelta

    def get_date_ago(base_dt, days: int) -> str:
        return (base_dt - timedelta(days=days)).strftime("%Y-%m-%d")

    result = None

    if intent.source == "alert" and intent.time_range:
        original_f_date, original_t_date = intent.time_range
        
        # 1. Fetch alerts for the user-specified range ("the date given")
        payload = build_combined_payload(
            intent=intent,
            plan=plan,
            vehicle=vehicle,
            company_id=company_id
        )
        logger.info(f"[SERVICE] Fetching alerts for requested range: {original_f_date} to {original_t_date}")
        res = combined_report(**payload)
        
        # Count matching alerts
        alerts_section = res.get("alerts", {}) if isinstance(res, dict) else {}
        alerts_list = alerts_section.get("results", []) if isinstance(alerts_section, dict) else []
        
        alert_focus = getattr(intent, "alert_focus", None)
        focus_clean = alert_focus.lower().replace("_", "").replace("-", "") if alert_focus else None
        
        if focus_clean:
            matching_count = 0
            for a in alerts_list:
                a_name = str(a.get("AlertName", "")).lower().replace("_", "").replace("-", "")
                if focus_clean in a_name or a_name in focus_clean:
                    matching_count += 1
        else:
            matching_count = len(alerts_list)

        logger.info(f"[SERVICE] User requested range found {matching_count} matching alerts.")
        
        # 2. If data is available, do NOT backoff
        if matching_count > 0:
            result = res
            result["backoff_applied"] = False
        else:
            # 3. No data available on given date or date range -> Perform dynamic backoff
            logger.info(f"[SERVICE] No alerts found on requested date/range. Initiating dynamic backoff...")
            
            # Base the backoff end date on the user's requested end date (t_date)
            try:
                base_dt = datetime.strptime(original_t_date, "%Y-%m-%d")
            except Exception:
                base_dt = datetime.now(timezone.utc)
                
            intervals = [
                (get_date_ago(base_dt, 7), original_t_date),
                (get_date_ago(base_dt, 14), original_t_date),
                (get_date_ago(base_dt, 30), original_t_date),
            ]
            
            backoff_successful = False
            for f_date, t_date in intervals:
                # Update time_range in plan and intent to query the API
                plan.time_range = (f_date, t_date)
                intent.time_range = (f_date, t_date)
                
                payload = build_combined_payload(
                    intent=intent,
                    plan=plan,
                    vehicle=vehicle,
                    company_id=company_id
                )
                
                logger.info(f"[SERVICE] Dynamic Backoff: Fetching alerts for range {f_date} to {t_date}")
                backoff_res = combined_report(**payload)
                
                # Count matching alerts in backoff result
                backoff_alerts_section = backoff_res.get("alerts", {}) if isinstance(backoff_res, dict) else {}
                backoff_alerts_list = backoff_alerts_section.get("results", []) if isinstance(backoff_alerts_section, dict) else []
                
                if focus_clean:
                    backoff_matching_count = 0
                    for a in backoff_alerts_list:
                        a_name = str(a.get("AlertName", "")).lower().replace("_", "").replace("-", "")
                        if focus_clean in a_name or a_name in focus_clean:
                            backoff_matching_count += 1
                else:
                    backoff_matching_count = len(backoff_alerts_list)
                    
                logger.info(f"[SERVICE] Backoff Range {f_date} to {t_date} found {backoff_matching_count} matching alerts.")
                
                if backoff_matching_count > 0:
                    result = backoff_res
                    result["backoff_applied"] = True
                    result["backoff_original_range"] = (original_f_date, original_t_date)
                    result["backoff_used_range"] = (f_date, t_date)
                    backoff_successful = True
                    break
            
            if not backoff_successful:
                # Exited loop without finding any matching alerts
                focus_name = f" {intent.alert_focus.replace('_', ' ')}" if getattr(intent, "alert_focus", None) else ""
                
                # Restore original time range to avoid modifying state on failures
                plan.time_range = (original_f_date, original_t_date)
                intent.time_range = (original_f_date, original_t_date)
                
                return {
                    "type": "error",
                    "message": f"Checked across the month (backing off from {original_t_date}) but did not see any{focus_name} alerts for vehicle {intent.vehicle_id}."
                }
    else:
        # Standard non-alert query flow
        payload = build_combined_payload(
            intent=intent,
            plan=plan,
            vehicle=vehicle,
            company_id=company_id
        )
        logger.info(f"[SERVICE] Payload: {payload}")
        result = combined_report(**payload)

    # logger.info(f"[SERVICE] API Result: {result}")

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    validation = validate_api_response(result)

    if validation["type"] == "error":

        return validation

    validated_data = validation["data"]

    # --------------------------------------------------
    # FORMAT RESPONSE
    # --------------------------------------------------

    return build_response(
        intent,
        validated_data
    )