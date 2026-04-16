import re
from datetime import datetime, timedelta
import dateparser


def normalize_time_text(text: str) -> str:
    return text.lower().strip()



def parse_time_range(text: str):
    text = normalize_time_text(text)

    now = datetime.now()

    # -----------------------------
    # CASE 1: between X and Y
    # -----------------------------
    match = re.search(r"between (.+?) and (.+)", text)
    if match:
        start_str, end_str = match.groups()

        start = dateparser.parse(start_str)
        end = dateparser.parse(end_str)

        if start and end:
            return start, end

    # -----------------------------
    # CASE 2: from X to Y
    # -----------------------------
    match = re.search(r"from (.+?) to (.+)", text)
    if match:
        start_str, end_str = match.groups()

        start = dateparser.parse(start_str)
        end = dateparser.parse(end_str)

        if start and end:
            return start, end

    # -----------------------------
    # CASE 3: since X → till today
    # -----------------------------
    match = re.search(r"(since|from) (.+)", text)
    if match:
        start_str = match.group(2)

        start = dateparser.parse(start_str)
        if start:
            return start, now

    # -----------------------------
    # CASE 4: last X days
    # -----------------------------
    match = re.search(r"last (\d+) days", text)
    if match:
        days = int(match.group(1))
        return now - timedelta(days=days), now

    # -----------------------------
    # FALLBACK (IMPORTANT)
    # -----------------------------
    parsed = dateparser.parse(text)

    if parsed:
        return parsed, parsed

    # -----------------------------
    # FINAL FAIL-SAFE (CRITICAL)
    # -----------------------------
    return now.replace(hour=0, minute=0, second=0), now