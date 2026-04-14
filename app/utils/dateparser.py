from datetime import datetime
import re
from dateutil import parser


def parse_time_range(time_range: str):
    if not time_range:
        return None, None

    now = datetime.now()

    try:
        # CASE 1: from X to Y
        match = re.search(r"from (.+?) to (.+)", time_range)
        if match:
            start_raw = match.group(1)
            end_raw = match.group(2)

            start_date = parser.parse(start_raw, default=now)
            end_date = parser.parse(end_raw, default=now)

            return start_date, end_date

        # CASE 2: since X
        match = re.search(r"(since|from) (.+)", time_range)
        if match:
            start_date = parser.parse(match.group(2), default=now)
            return start_date, now

        # CASE 3: today
        if "today" in time_range:
            return now, now

        # CASE 4: yesterday
        if "yesterday" in time_range:
            y = now.replace(day=now.day - 1)
            return y, y

    except Exception as e:
        print("Date parsing error:", e)

    return None, None