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

def build_google_maps_url(location) -> str:

    try:

        if not location:
            return ""

        # -------------------------------------------------
        # STRING FORMAT
        # -------------------------------------------------

        if isinstance(location, str):

            parts = [
                p.strip()
                for p in location.split(",")
            ]

            if len(parts) != 2:
                return ""

            lat, lng = parts

            float(lat)
            float(lng)

            return (
                "https://maps.google.com/?q="
                f"{lat},{lng}"
            )

        # -------------------------------------------------
        # DICT FORMAT
        # -------------------------------------------------

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

            float(lat)
            float(lng)

            return (
                "https://maps.google.com/?q="
                f"{lat},{lng}"
            )

        return ""

    except Exception:

        return ""