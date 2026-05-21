from datetime import datetime
import re


# =========================================================
# HELPERS
# =========================================================

def parse_alert_date(date_str: str):

    if not date_str:
        return datetime.min

    try:

        return datetime.fromisoformat(
            date_str.replace("Z", "+00:00")
        )

    except Exception:

        return datetime.min


def extract_date_only(date_str: str) -> str:

    parsed = parse_alert_date(date_str)

    if parsed == datetime.min:
        return "Unknown"

    return parsed.strftime("%Y-%m-%d")


def convert_duration_to_seconds(
    duration: str | None
) -> int:

    if not duration:
        return 0

    hours = 0
    minutes = 0
    seconds = 0

    hr_match = re.search(
        r"(\d+)\s*hr",
        duration,
        re.IGNORECASE
    )

    min_match = re.search(
        r"(\d+)\s*min",
        duration,
        re.IGNORECASE
    )

    sec_match = re.search(
        r"(\d+)\s*sec",
        duration,
        re.IGNORECASE
    )

    if hr_match:
        hours = int(hr_match.group(1))

    if min_match:
        minutes = int(min_match.group(1))

    if sec_match:
        seconds = int(sec_match.group(1))

    return (
        hours * 3600
        + minutes * 60
        + seconds
    )


def safe_float(value):

    try:
        return float(value)

    except Exception:
        return 0.0
