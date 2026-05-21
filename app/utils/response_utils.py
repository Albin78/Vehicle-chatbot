from app.utils.logger import logger


def error_response(message: str):

    logger.error(message)

    return {
        "type": "error",
        "message": message
    }


def success_response(response_type: str, data: dict):

    return {
        "type": response_type,
        "data": data
    }


# =========================================================
# LOCATION FORMATTER
# =========================================================

def build_google_maps_url(
    location
) -> str:

    if not location:
        return ""

    # -----------------------------------------------------
    # STRING FORMAT:
    # "26.42683, 50.0109466"
    # -----------------------------------------------------

    if isinstance(location, str):

        parts = [
            p.strip()
            for p in location.split(",")
        ]

        if len(parts) != 2:
            return ""

        lat, lng = parts

        try:

            float(lat)
            float(lng)

        except Exception:

            return ""

        return (
            "https://maps.google.com/?q="
            f"{lat},{lng}"
        )

    # -----------------------------------------------------
    # DICT FORMAT
    # {"latitude": ..., "longitude": ...}
    # -----------------------------------------------------

    if isinstance(location, dict):

        lat = (
            location.get("latitude")
            or location.get("lat")
        )

        lng = (
            location.get("longitude")
            or location.get("lng")
            or location.get("lon")
        )

        if lat is None or lng is None:
            return ""

        try:

            float(lat)
            float(lng)

        except Exception:

            return ""

        return (
            "https://maps.google.com/?q="
            f"{lat},{lng}"
        )

    return ""