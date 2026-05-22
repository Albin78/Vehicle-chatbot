from app.utils.response_utils import build_google_maps_url
from app.parsers.date_parser import format_time_generate

def safe_format_date(value) -> str:
    if not value:
        return ""
    try:
        formatted = format_time_generate(value)
        return formatted or str(value)
    except Exception:
        return str(value)

def format_idling_summary(result, intent):
    try:
        if not isinstance(result, dict):
            return "Invalid alert response format."

        vehicle = result.get("vehicle") or intent.vehicle_id or "Unknown"
        idling = result.get("idling") or {}
        count = idling.get("count", 0)
        longest_seconds = idling.get("longest_seconds", 0)
        longest = idling.get("longest")

        insights = [
            f"Idling Summary for Vehicle {vehicle}:",
            f"- Total Idling Alerts: {count}",
            f"- Longest Idling Duration: {longest_seconds} seconds"
        ]

        if longest:
            longest_parts = []
            duration = longest.get("duration")
            if duration:
                longest_parts.append(f"duration {duration}")

            event_time = longest.get("time")
            if event_time:
                formatted_time = safe_format_date(event_time)
                if formatted_time:
                    longest_parts.append(f"on {formatted_time}")

            location = longest.get("location")
            if location:
                google_maps_url = build_google_maps_url(location)
                if google_maps_url:
                    longest_parts.append(f"location: {google_maps_url}")

            if longest_parts:
                insights.append(f"- Longest Idling Event: {', '.join(longest_parts)}")

        return "\n".join(insights)

    except Exception as e:
        return f"Unable to format idling summary: {str(e)}"
