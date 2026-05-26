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