from datetime import datetime


def format_last_updated(timestamp: str):

    if not timestamp:
        return None

    try:

        dt = datetime.strptime(
            timestamp,
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )

        return dt.strftime(
            "%b %d, %Y %I:%M %p UTC"
        )

    except Exception:

        return timestamp
    


def build_location(lat: float, lon: float):


    if not lat or not lon:
        return None

    try:

        lat = float(lat)
        lon = float(lon)

        return {
            "latitude": lat,
            "longitude": lon,
            "google_maps_url":
                f"https://www.google.com/maps?q={lat},{lon}"
        }
    
    except Exception:

        return None