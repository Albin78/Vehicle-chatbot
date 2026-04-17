import re
from datetime import datetime, timedelta
import dateparser


def normalize_time_text(text: str) -> str:
    if text:
        return text.lower().strip()
    return "Date is not fetched"


def parse_time_range(text: str):
    text = normalize_time_text(text)
    now = datetime.now()

    settings = {
        "PREFER_DATES_FROM": "current_period",
        "RELATIVE_BASE": now,
    }

    # -----------------------------
    # CASE 1: "from X to Y"
    # -----------------------------
    match = re.search(r"from (.+?) to (.+)", text)
    if match:
        start_str, end_str = match.groups()

        start = dateparser.parse(start_str, settings=settings)  # type: ignore

        if start and not re.search(r"[a-zA-Z]", end_str):
            end_str = start.strftime("%B") + " " + end_str

        end = dateparser.parse(end_str, settings=settings)   # type: ignore

        if start and end:
            return finalize_dates(start, end, now)

    # -----------------------------
    # CASE 2: "april 1-10"
    # -----------------------------
    match = re.search(r"([a-zA-Z]+)\s*(\d{1,2})\s*[-]\s*(\d{1,2})", text)
    if match:
        month, start_day, end_day = match.groups()

        start_str = f"{month} {start_day}"
        end_str = f"{month} {end_day}"

        start = dateparser.parse(start_str, settings=settings)  # type: ignore
        end = dateparser.parse(end_str, settings=settings)     # type: ignore

        if start and end:
            return finalize_dates(start, end, now)

    # -----------------------------
    # CASE 3: "april 1 to 10"
    # -----------------------------
    match = re.search(r"([a-zA-Z]+)\s*(\d{1,2})\s*(to)\s*(\d{1,2})", text)
    if match:
        month, start_day, _, end_day = match.groups()

        start_str = f"{month} {start_day}"
        end_str = f"{month} {end_day}"

        start = dateparser.parse(start_str, settings=settings)   # type: ignore
        end = dateparser.parse(end_str, settings=settings)       # type: ignore
 
        if start and end:
            return finalize_dates(start, end, now)

    # -----------------------------
    # CASE 4: last X days
    # -----------------------------
    match = re.search(r"last (\d+) days", text)
    if match:
        days = int(match.group(1))
        start = now - timedelta(days=days)
        end = now
        return format_dates(start, end)

    # -----------------------------
    # FALLBACK
    # -----------------------------
    parsed = dateparser.parse(text, settings=settings)  # type: ignore

    if parsed:
        return format_dates(parsed, parsed)

    return None, None




def finalize_dates(start, end, now):
    start = start.replace(year=now.year)
    end = end.replace(year=now.year)

    return format_dates(start, end)


def format_dates(start, end):
    return (
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d")
    )