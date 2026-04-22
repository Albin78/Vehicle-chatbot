import re
import calendar
from datetime import datetime



MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12
}


def is_time_range_in_query(query: str) -> bool:
    query = query.lower()

    patterns = [
        r"\bbetween\b",
        r"\bfrom\b",
        r"\bto\b",
        r"\b\d{1,2}\b",            
        r"\bjan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec\b"
    ]

    return any(re.search(p, query) for p in patterns)



def normalize_time_expression(query: str) -> str:
    query = query.lower()

    # Normalize connectors
    query = re.sub(r"\bbetween\b", "", query)
    query = re.sub(r"\band\b", "to", query)
    query = re.sub(r"\btill\b|\buntil\b|\bthrough\b", "to", query)

    # Normalize separators
    query = re.sub(r"\s*-\s*", " to ", query)

    # Collapse spaces
    query = re.sub(r"\s+", " ", query)

    return query.strip()



def validate_day(year: int, month: int, day: int) -> int:
    max_day = calendar.monthrange(year, month)[1]

    if day < 1:
        return 1

    if day > max_day:
        return max_day   # clamp to last valid day

    return day


def build_date_range(year, month, d1, d2):
    month_num = MONTH_MAP[month[:3]]

    year = int(year)
    d1 = int(d1)
    d2 = int(d2)

    # ✅ Validate days
    d1 = validate_day(year, month_num, d1)
    d2 = validate_day(year, month_num, d2)

    # Optional: ensure correct ordering
    if d1 > d2:
        d1, d2 = d2, d1

    start = datetime(year, month_num, d1)
    end = datetime(year, month_num, d2)

    return (
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d")
    )


def extract_time_range(query: str):

    if isinstance(query, tuple):
        return query 
    
    if isinstance(query, str):
        query = normalize_time_expression(query)

        current_year = datetime.now().year

        pattern = re.search(
            r"(?:(\d{4})\s+)?"                       # optional year prefix
            r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+"
            r"(\d{1,2})\s+to\s+(\d{1,2})"
            r"(?:\s+(\d{4}))?",                     # optional year suffix
            query
        )

        if not pattern:
            return None

        year_prefix, month, d1, d2, year_suffix = pattern.groups()

        # Resolve year
        if year_prefix:
            year = year_prefix
        elif year_suffix:
            year = year_suffix
        else:
            year = str(current_year)

        return build_date_range(year, month, d1, d2)
    
    return None



def format_time_range(time_range):
    if not time_range:
        return ""

    if isinstance(time_range, tuple):
        start, end = time_range

        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            end_dt = datetime.strptime(end, "%Y-%m-%d")

            # Example: January 21 to January 30
            return f"{start_dt.strftime('%B %d')} to {end_dt.strftime('%B %d')}"

        except Exception:
            return str(time_range)

    return str(time_range)