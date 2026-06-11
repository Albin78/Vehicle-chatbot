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

    def _format_driver(driver: any) -> str:
        if not driver or str(driver).lower() in ("null", "na", "unknown", "none", "unassigned", "undefined"):
            return ""
        import re
        d_str = " ".join(str(driver).split())
        return re.sub(r'\s*\([^)]*\)', '', d_str).strip()

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
        
        driver_formatted = _format_driver(driver)
        is_driver_unavailable = not driver_formatted
        
        # Check if the metric value is 0 (meaning no activity occurred)
        if val in (0, "0", "0s", 0.0) and q_type.startswith("top_"):
            return f"No {subject}s recorded any {metric} {tr_str}."
        
        if q_type in ("top_alert_vehicle", "top_alert_driver"):
            
            dist = result.get("alertDistribution", {})
            dist_str = ""
            if dist:
                dist_str = " Breakdown: " + ", ".join(f"{k}: {v}" for k, v in dist.items()) + "."
                
            if q_type == "top_alert_driver":
                driver_display = "driver details not currently available" if is_driver_unavailable else f"'{driver_formatted}'"
                if plate and plate != "Unknown" and plate != "Unknown Vehicle":
                    return (
                        f"Driver {driver_display} (in vehicle {plate}{group_str}) had {qualifier} number of {metric} "
                        f"with a total of {val} {tr_str}.{dist_str}"
                    )
                else:
                    return (
                        f"Driver {driver_display}{group_str} had {qualifier} number of {metric} "
                        f"with a total of {val} {tr_str}.{dist_str}"
                    )
            else:
                driver_str = f" (driver details not currently available)" if is_driver_unavailable else f" (Driver: '{driver_formatted}')"
                return (
                    f"Vehicle {plate}{driver_str}{group_str} had {qualifier} number of {metric} "
                    f"with a total of {val} {tr_str}.{dist_str}"
                )
        else:
            if subject == "driver":
                driver_display = "driver details not currently available" if is_driver_unavailable else f"'{driver_formatted}'"
                return (
                    f"Driver {driver_display} (in vehicle {plate}{group_str}) had {qualifier} {metric} "
                    f"with a value of {val} {tr_str}."
                )
            else:
                driver_str = f" (driver details not currently available)" if is_driver_unavailable else f" driven by '{driver_formatted}'"
                return (
                    f"Vehicle {plate}{driver_str}{group_str} had {qualifier} {metric} "
                    f"with a value of {val} {tr_str}."
                )

    if q_type == "fleet_status_list":
        status = result.get("status", "unknown")
        count = result.get("count", 0)
        vehicles = result.get("vehicles", [])
        subject = result.get("subject", "vehicle")
        
        if count == 0:
            return f"Currently, there are no {subject}s with the status '{status}'."
            
        def format_v(v):
            np = v.get('numberPlate', 'Unknown')
            dn = _format_driver(v.get('driverName'))
            
            if subject == "driver":
                return f"{dn} (Vehicle: {np})" if dn else f"Unknown Driver (Vehicle: {np})"
            else:
                return f"{np} (Driver: {dn})" if dn else np
            
        vehicle_list_str = ", ".join(format_v(v) for v in vehicles[:20])
        if count > 20:
            vehicle_list_str += f" and {count - 20} more"
            
        return f"Currently, there are {count} {subject}s with the status '{status}': {vehicle_list_str}."

    if q_type == "fleet_metrics_list":
        metrics_req = result.get("metrics_requested", [])
        vehicles = result.get("vehicles", [])
        filt = result.get("filter", "")
        
        if not vehicles:
            return f"No live data found for the requested metrics {tr_str}."
            
        filter_target_value = None
        if filt in ("on", "open", "fastened", "enabled"):
            filter_target_value = "1"
        elif filt in ("off", "closed", "unfastened", "disabled"):
            filter_target_value = "0"
            
        lines = []
        import re
        for v in vehicles:
            plate = v.get("numberPlate") or v.get("vehicleName") or "Unknown"
            include_vehicle = True
            
            if "remote_immobilization" in metrics_req:
                immob_val = str(v.get("RemoteImmobilaztion")).strip()
                enabled_val = str(v.get("RemoteImmobilaztionEnabled")).strip()
                
                if filter_target_value and immob_val != filter_target_value:
                    include_vehicle = False
                
                immob_status = "Not Immobilized"
                if immob_val == "1":
                    immob_status = "Immobilized"
                elif immob_val in ("None", "NA", "N/A", "null", ""):
                    immob_status = "Status Unknown"
                    
                enabled_status = "Feature Disabled"
                if enabled_val == "1":
                    enabled_status = "Feature Enabled"
                elif enabled_val in ("None", "NA", "N/A", "null", ""):
                    enabled_status = "Feature Status Unknown"
                    
                v["RemoteImmobilaztion_formatted"] = f"{immob_status}, {enabled_status}"
                
            if "seatbelt" in metrics_req:
                belt_val = v.get("seatBelt")
                enabled_val = v.get("SeatbeltEnabledIo")
                
                def is_invalid(val):
                    if val is None: return True
                    if isinstance(val, str) and val.strip().lower() in ("", "na", "null", "nan"): return True
                    return False
                
                belt_invalid = is_invalid(belt_val)
                enabled_invalid = is_invalid(enabled_val)
                
                b_str = str(belt_val).strip().split(".")[0] if not belt_invalid else ""
                e_str = str(enabled_val).strip().split(".")[0] if not enabled_invalid else ""
                
                if enabled_invalid:
                    if belt_invalid:
                        seatbelt_status = "Status Unknown"
                        if filt:
                            include_vehicle = False
                    elif b_str == "1":
                        seatbelt_status = "Fastened"
                        if filt in ("unfastened", "disabled"):
                            include_vehicle = False
                    elif b_str == "0":
                        seatbelt_status = "Unfastened"
                        if filt in ("fastened", "disabled", "enabled"):
                            include_vehicle = False
                elif e_str == "0":
                    if b_str == "0":
                        seatbelt_status = "Not Enabled and Not Fastened"
                    else:
                        seatbelt_status = "Not Enabled"
                        
                    if filt not in ("", "disabled"):
                        include_vehicle = False
                elif e_str == "1":
                    if belt_invalid:
                        seatbelt_status = "Status Unknown"
                        if filt:
                            include_vehicle = False
                    elif b_str == "1":
                        seatbelt_status = "Enabled and Fastened"
                        if filt not in ("", "fastened", "enabled"):
                            include_vehicle = False
                    elif b_str == "0":
                        seatbelt_status = "Enabled but Not Fastened"
                        if filt not in ("", "unfastened", "enabled"):
                            include_vehicle = False
                    else:
                        seatbelt_status = b_str
                        
                v["Seatbelt_formatted"] = seatbelt_status
            
            parts = []
            for key, val in v.items():
                if key in ("vehicleName", "numberPlate", "driverName", "lastUpdated", "RemoteImmobilaztion", "RemoteImmobilaztionEnabled", "RemoteImmobilaztion_formatted", "seatBelt", "SeatbeltEnabledIo", "Seatbelt_formatted"):
                    continue
                    
                val_str = "Unknown"
                if val in (None, "NA", "N/A", "null", ""):
                    val_str = "Currently Unavailable"
                    if filter_target_value:
                        include_vehicle = False
                elif str(val) in ("0", "1", "0.0", "1.0", "True", "False"):
                    if str(val) == "True": b_val = "1"
                    elif str(val) == "False": b_val = "0"
                    else: b_val = str(val).split(".")[0]
                    
                    if filter_target_value and b_val != filter_target_value:
                        include_vehicle = False
                        
                    if "door" in key.lower():
                        val_str = "Open" if b_val == "1" else "Closed"
                    elif "seatbelt" in key.lower() or "seat" in key.lower():
                        val_str = "Fastened" if b_val == "1" else "Unfastened"
                    else:
                        val_str = "On" if b_val == "1" else "Off"
                else:
                    val_str = str(val)
                    
                display_key = key.replace("On", "").replace("Status", "").replace("Level", " Level")
                display_key = re.sub(r"([a-z])([A-Z])", r"\1 \2", display_key).strip().title()
                
                parts.append(f"{display_key}: {val_str}")
            
            if not include_vehicle:
                continue
                
            if "remote_immobilization" in metrics_req:
                parts.insert(0, f"Remote Immobilization: {v.get('RemoteImmobilaztion_formatted')}")
                
            if "seatbelt" in metrics_req:
                parts.insert(0, f"Seat Belt: {v.get('Seatbelt_formatted')}")
                
            metrics_str = " | ".join(parts)
            lines.append(f"- Vehicle {plate}: {metrics_str}")
            
        metrics_name = ", ".join(m.replace("_", " ") for m in metrics_req).title()
        filter_str = f" that are currently {filt}" if filt else ""
        
        if not lines:
            return f"Currently, there are no vehicles with a {metrics_name.lower()} status{filter_str}."
            
        header = f"Live {metrics_name.lower()} status{filter_str} for the fleet {tr_str}:\n"
        
        if len(lines) > 30:
            lines = lines[:30] + [f"...and {len(vehicles) - 30} more vehicles."]
            
        return header + "\n".join(lines)

    if q_type and q_type.startswith("ranked_"):
        ranked_list = result.get("ranked", [])
        raw_metric = q_type.replace("ranked_", "")
        
        metric_map = {
            "idleTime": "idle time",
            "movingTime": "moving time",
            "stopTime": "stop time",
            "engineHours": "engine hours",
            "maxSpeed": "maximum speed",
            "speed": "maximum speed",
            "distance": "distance traveled"
        }
        metric_display = metric_map.get(raw_metric, raw_metric.replace("_", " "))
        
        if not ranked_list:
            return f"No ranking data available for {metric_display} {tr_str}."
            
        lines = []
        for item in ranked_list:
            rank = item.get("rank")
            plate = item.get("numberPlate", "Unknown")
            driver_formatted = _format_driver(item.get("driverName"))
            driver_str = "" if not driver_formatted else f" (Driver: {driver_formatted})"
            
            val = _format_value("value", item.get("value", 0), raw_metric)
            lines.append(f"{rank}. Vehicle {plate}{driver_str} - {val}")
            
        header = f"Here is the top {len(ranked_list)} ranking for highest {metric_display} {tr_str}:\n"
        return header + "\n".join(lines)

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
