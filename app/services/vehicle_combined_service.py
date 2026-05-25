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

    def get_date_ago(days: int) -> str:
        return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    should_backoff = False
    if intent.source == "alert" and intent.time_range:
        f_date, t_date = intent.time_range
        if f_date == t_date:  # today only, or latest query
            should_backoff = True

    if should_backoff:
        intervals = [
            (today_str, today_str),
            (get_date_ago(7), today_str),
            (get_date_ago(14), today_str),
            (get_date_ago(30), today_str),
        ]
        
        result = None
        for f_date, t_date in intervals:
            # Temporarily update time_range to query the API
            plan.time_range = (f_date, t_date)
            intent.time_range = (f_date, t_date)
            
            payload = build_combined_payload(
                intent=intent,
                plan=plan,
                vehicle=vehicle,
                company_id=company_id
            )
            
            logger.info(f"[SERVICE] Dynamic Backoff: Fetching alerts for range {f_date} to {t_date}")
            res = combined_report(**payload)
            
            # Count matching alerts
            alerts_section = res.get("alerts", {}) if isinstance(res, dict) else {}
            alerts_list = alerts_section.get("results", []) if isinstance(alerts_section, dict) else []
            
            alert_focus = getattr(intent, "alert_focus", None)
            if alert_focus:
                focus_clean = alert_focus.lower().replace("_", "").replace("-", "")
                matching_count = 0
                for a in alerts_list:
                    a_name = str(a.get("AlertName", "")).lower().replace("_", "").replace("-", "")
                    if focus_clean in a_name or a_name in focus_clean:
                        matching_count += 1
            else:
                matching_count = len(alerts_list)
                
            logger.info(f"[SERVICE] Range {f_date} to {t_date} found {matching_count} matching alerts.")
            result = res
            
            if matching_count > 0:
                break
        else:
            # Exited loop without finding any matching alerts
            focus_name = f" {intent.alert_focus.replace('_', ' ')}" if getattr(intent, "alert_focus", None) else ""
            return {
                "type": "error",
                "message": f"Checked across the month but did not see any{focus_name} alerts for vehicle {intent.vehicle_id}."
            }
    else:
        # Standard query flow
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