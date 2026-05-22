from app.utils.response_utils import build_google_maps_url
from app.utils.logger import logger
from app.parsers.date_parser import format_time_generate

def safe_format_date(value) -> str:
    if not value:
        return ""
    try:
        formatted = format_time_generate(value)
        return formatted or str(value)
    except Exception:
        return str(value)

def format_overspeed_summary(result, intent):
    try:
        if not isinstance(result, dict):
            return "Invalid alert response format."

        overspeed = result.get("overspeed") or {}
        count = overspeed.get("count", 0)
        highest = overspeed.get("highest") or {}
        highest_speed = highest.get("speed") or f"{overspeed.get('highest_value', 0)} km/h"
        
        highest_location = highest.get("location")
        highest_map_url = build_google_maps_url(highest_location) if highest_location else ""

        latest = result.get("latest_alert") or {}
        driver_name = latest.get("DriverName") or "Unknown"
        group_name = latest.get("GroupName") or "Unknown"
        latest_date = latest.get("Date")
        formatted_date = safe_format_date(latest_date) if latest_date else ""
        
        latest_location = latest.get("Location")
        latest_map_url = build_google_maps_url(latest_location) if latest_location else ""

        # Daily alerts formatting
        daily_alerts = result.get("daily_alerts") or {}
        daily_parts = []
        if daily_alerts:
            # Sort descending
            sorted_days = sorted(daily_alerts.items(), key=lambda x: x[0], reverse=True)
            for day, day_count in sorted_days:
                formatted_day = safe_format_date(day) or day
                daily_parts.append(f"{formatted_day} ({day_count} alerts)")
        daily_formatted = ", ".join(daily_parts) if daily_parts else "None"

        insights = [
            f"Overspeed Summary for Vehicle {intent.vehicle_id}:",
            f"- Total Overspeed Count: {count}",
            f"- Highest Speed Reached: {highest_speed}"
        ]

        if highest_map_url:
            insights.append(f"- Highest Speed Location: {highest_map_url}")
            
        if highest.get("time"):
            formatted_highest_time = safe_format_date(highest.get("time"))
            insights.append(f"- Highest Speed Time: {formatted_highest_time}")

        insights.append(f" Latest Alert Date: {formatted_date}")
        insights.append(f" Driver: {driver_name}")
        insights.append(f"Group: {group_name}")

        if latest_map_url:
            insights.append(f"Alert Location: {latest_map_url}")

        insights.append(f"- Daily Alerts Breakdown: {daily_formatted}")

        return "\n".join(insights)

    except Exception as e:
        logger.error(f"Error formatting overspeed summary: {e}", exc_info=True)
        return f"Unable to format overspeed summary: {str(e)}"
