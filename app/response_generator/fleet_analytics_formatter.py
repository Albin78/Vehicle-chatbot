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
    tr_str = f"from {time_range[0]} to {time_range[1]}" if isinstance(time_range, tuple) and len(time_range) == 2 else ""

    if q_type == "fleet_overview":
        overview = result.get("overview", {})
        totals = result.get("totals", {})
        return (
            f"Fleet overview {tr_str}: "
            f"Total vehicles: {overview.get('total', 0)}. "
            f"Moving: {overview.get('moving', 0)}. "
            f"Idle: {overview.get('idle', 0)}. "
            f"Stopped: {overview.get('stopped', 0)}. "
            f"Out of network: {overview.get('out_network', 0)}. "
            f"Disconnected: {overview.get('disconnected', 0)}. "
            f"Total distance: {totals.get('distance', 0)} km. "
            f"Total idle time: {_format_value('idleTime', totals.get('idleTime', 0))}. "
            f"Total stop time: {_format_value('stopTime', totals.get('stopTime', 0))}. "
            f"Total moving time: {_format_value('movingTime', totals.get('movingTime', 0))}."
        )

    if q_type == "fleet_alert_count":
        dist = result.get("distribution", {})
        dist_str = ", ".join(f"{k}: {v}" for k, v in dist.items())
        return (
            f"There were {result.get('totalAlerts', 0)} alerts {tr_str}. "
            f"Alert distribution: {dist_str}."
        )

    # For top_speed, top_idle_time, top_distance, etc.
    if q_type and (q_type.startswith("top_") or q_type.startswith("bottom_")):
        subject = result.get("subject", "vehicle")
        plate = result.get("numberPlate", "Unknown")
        driver = result.get("driverName")
        val = _format_value('value', result.get('value', 0), result.get('metric'))
        metric = result.get("metric", "").replace("_", " ")
        qualifier = "the highest" if q_type.startswith("top_") else "the lowest"
        
        if subject == "driver":
            driver_display = driver if driver else "Unknown Driver"
            return (
                f"Driver '{driver_display}' (in vehicle {plate}) had {qualifier} {metric} "
                f"with a value of {val} {tr_str}."
            )
        else:
            driver_str = f" driven by {driver}" if driver else " (Driver: Unknown)"
            return (
                f"Vehicle {plate}{driver_str} had {qualifier} {metric} "
                f"with a value of {val} {tr_str}."
            )

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
