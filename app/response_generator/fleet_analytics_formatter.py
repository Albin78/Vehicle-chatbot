def format_fleet_analytics(result: dict) -> str:
    """
    Converts the fleet_analytics result dict to clear English sentences.
    This provides the LLM with a robust, pre-formatted natural language base.
    """
    def _format_value(k: str, v: any, metric: str = None) -> any:
        time_keys = {"idletime", "stoptime", "movingtime", "enginehours"}
        speed_keys = {"speed", "maxspeed", "averagespeed"}
        dist_keys = {"distance", "distancetravelled"}
        
        is_time = k.lower() in time_keys or (k.lower() == "value" and metric and metric.lower() in time_keys)
        is_speed = k.lower() in speed_keys or (k.lower() == "value" and metric and metric.lower() in speed_keys)
        is_dist = k.lower() in dist_keys or (k.lower() == "value" and metric and metric.lower() in dist_keys)
        
        if is_time and isinstance(v, (int, float)):
            total_seconds = int(v)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if hours > 0:
                return f"{hours} hours {minutes} minutes"
            return f"{minutes} minutes"
        elif is_speed and isinstance(v, (int, float)):
            return f"{v} km/h"
        elif is_dist and isinstance(v, (int, float)):
            return f"{v} km"
            
        return v

    q_type = result.get("query_type")
    time_range = result.get("time_range", ("", ""))
    tr_str = ""
    if isinstance(time_range, tuple) and len(time_range) == 2:
        start_date, end_date = time_range
        if start_date and end_date:
            if start_date == end_date:
                tr_str = f"on {start_date}"
            else:
                tr_str = f"from {start_date} to {end_date}"

    if q_type == "fleet_overview":
        overview = result.get("overview", {})
        totals = result.get("totals", {})
        alerts_total = result.get("alerts_total", 0)
        dist = result.get("alerts_distribution", {})
        
        dist_str = ", ".join(f"{k}: {v}" for k, v in dist.items()) if dist else "None"
        
        return (
            f"Fleet overview {tr_str}:\n"
            f"- Current Status: Total {overview.get('total', 0)} vehicles "
            f"(Moving: {overview.get('moving', 0)}, Idle: {overview.get('idle', 0)}, "
            f"Stopped: {overview.get('stopped', 0)}, Out of network: {overview.get('out_network', 0)}, "
            f"Disconnected: {overview.get('disconnected', 0)}).\n"
            f"- Operations: Total distance {totals.get('totalDistance', 0)} km. "
            f"Idle time: {totals.get('totalIdleTime', '0s')}. "
            f"Stop time: {totals.get('totalStopTime', '0s')}. "
            f"Moving time: {totals.get('totalMovingTime', '0s')}. "
            f"Engine hours: {totals.get('totalEngineHours', '0s')}.\n"
            f"- Alerts: {alerts_total} total alerts ({dist_str})."
        )

    if q_type == "fleet_alert_count":
        dist = result.get("distribution", {})
        dist_str = ", ".join(f"{k}: {v}" for k, v in dist.items())
        return (
            f"There were {result.get('totalAlerts', 0)} alerts {tr_str}. "
            f"Alert distribution: {dist_str}."
        )

    if q_type == "fleet_alert_distribution":
        dist = result.get("distribution", {})
        if not dist:
            return f"There were no alerts recorded {tr_str}."
            
        most_frequent_alert = max(dist.items(), key=lambda x: x[1])
        dist_str = ", ".join(f"{k}: {v}" for k, v in dist.items())
        return (
            f"The most frequent alert {tr_str} was '{most_frequent_alert[0]}' with {most_frequent_alert[1]} occurrences. "
            f"The full alert distribution is: {dist_str}."
        )

    # For top_speed, top_idle_time, top_distance, etc.
    if q_type and (q_type.startswith("top_") or q_type.startswith("bottom_")):
        subject = result.get("subject", "vehicle")
        plate = result.get("numberPlate", "Unknown")
        driver = result.get("driverName") 
        group = result.get("groupName")
        group_str = f" (Group: '{group}')" if group and group not in ("Unknown", "None", "") else ""
        
        if q_type in ("top_alert_vehicle", "top_alert_driver"):
            val = result.get('alertCount', 0)
            alert_type = result.get('alertType', 'all')
            metric = "alerts" if alert_type == "all" else f"{alert_type} alerts"
        else:
            val = _format_value('value', result.get('value', 0), result.get('metric'))
            raw_metric = result.get("metric", "")
            metric_map = {
                "idleTime": "idle time",
                "movingTime": "moving time",
                "stopTime": "stop time",
                "engineHours": "engine hours",
                "maxSpeed": "maximum speed",
                "distance": "distance traveled"
            }
            metric = metric_map.get(raw_metric, raw_metric.replace("_", " "))
            
        qualifier = "the highest" if q_type.startswith("top_") else "the lowest"
        
        if driver and isinstance(driver, str):
            driver = " ".join(driver.split())
            
        is_driver_unavailable = not driver or str(driver).lower() in ("null", "na", "unknown", "none", "unassigned", "undefined")
        
        # Check if the metric value is 0 (meaning no activity occurred)
        if val in (0, "0", "0s", 0.0) and q_type.startswith("top_"):
            return f"No {subject}s recorded any {metric} {tr_str}."
        
        if q_type in ("top_alert_vehicle", "top_alert_driver"):
            if q_type == "top_alert_driver":
                driver_display = "driver details not currently available" if is_driver_unavailable else f"'{driver}'"
                if plate and plate != "Unknown" and plate != "Unknown Vehicle":
                    return (
                        f"Driver {driver_display} (in vehicle {plate}{group_str}) had {qualifier} number of {metric} "
                        f"with a total of {val} {tr_str}."
                    )
                else:
                    return (
                        f"Driver {driver_display}{group_str} had {qualifier} number of {metric} "
                        f"with a total of {val} {tr_str}."
                    )
            else:
                driver_str = f" (driver details not currently available)" if is_driver_unavailable else f" (Driver: '{driver}')"
                return (
                    f"Vehicle {plate}{driver_str}{group_str} had {qualifier} number of {metric} "
                    f"with a total of {val} {tr_str}."
                )
        else:
            if subject == "driver":
                driver_display = "driver details not currently available" if is_driver_unavailable else f"'{driver}'"
                return (
                    f"Driver {driver_display} (in vehicle {plate}{group_str}) had {qualifier} {metric} "
                    f"with a value of {val} {tr_str}."
                )
            else:
                driver_str = f" (driver details not currently available)" if is_driver_unavailable else f" driven by '{driver}'"
                return (
                    f"Vehicle {plate}{driver_str}{group_str} had {qualifier} {metric} "
                    f"with a value of {val} {tr_str}."
                )

    if q_type == "fleet_status_list":
        status = result.get("status", "unknown")
        count = result.get("count", 0)
        vehicles = result.get("vehicles", [])
        
        if count == 0:
            return f"Currently, there are no vehicles with the status '{status}'."
            
        vehicle_list_str = ", ".join(v.get('numberPlate', 'Unknown') for v in vehicles[:20])
        if count > 20:
            vehicle_list_str += f" and {count - 20} more"
            
        return f"Currently, there are {count} vehicles with the status '{status}': {vehicle_list_str}."

    # Fallback to key-value string but cleaned up
    parts = []
    for k, v in result.items():
        if k in ("type", "vehicleName", "query_type", "subject"):
            continue
        if isinstance(v, (dict, list, tuple)):
            parts.append(f"{k}: {v}")
        else:
            parts.append(f"{k}: {_format_value(k, v, result.get('metric'))}")
            
    return "Fleet analytics data: " + ", ".join(parts) + "."
