import re
import calendar
from datetime import datetime, timedelta    
from typing import Union, Tuple, Optional



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


def extract_relative_time(query: str):
    query = query.lower()
    today = datetime.now().date()

    if "today" in query:
        return (str(today), str(today))

    if "yesterday" in query:
        y = today - timedelta(days=1)
        return (str(y), str(y))

    match = re.search(r"last\s+(\d+)\s+days", query)
    if match:
        days = int(match.group(1))
        start = today - timedelta(days=days)
        return (str(start), str(today))

    return None


def extract_single_date(query: str):
    query = query.lower()
    current_year = datetime.now().year

    pattern = re.search(
        r"(?:on\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:\s+(\d{4}))?",
        query
    )

    if not pattern:
        return None

    month, day, year = pattern.groups()

    year = int(year) if year else current_year
    month_num = MONTH_MAP[month[:3]]
    day = validate_day(year, month_num, int(day))

    date_str = datetime(year, month_num, day).strftime("%Y-%m-%d")

    return (date_str, date_str)


def extract_range_date(query: str):
    current_year = datetime.now().year

    # -----------------------------
    # CASE 1: "april 1 to april 18"
    # -----------------------------
    pattern_full = re.search(
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})\s+to\s+"
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})"
        r"(?:\s+(\d{4}))?",
        query
    )

    if pattern_full:
        m1, d1, m2, d2, year = pattern_full.groups()
        year = int(year) if year else current_year

        start = datetime(year, MONTH_MAP[m1[:3]], validate_day(year, MONTH_MAP[m1[:3]], int(d1)))
        end = datetime(year, MONTH_MAP[m2[:3]], validate_day(year, MONTH_MAP[m2[:3]], int(d2)))

        return (
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d")
        )

    # -----------------------------
    # CASE 2: "april 1 to 18"
    # -----------------------------
    pattern_same_month = re.search(
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+"
        r"(\d{1,2})\s+to\s+(\d{1,2})"
        r"(?:\s+(\d{4}))?",
        query
    )

    if pattern_same_month:
        month, d1, d2, year = pattern_same_month.groups()
        year = int(year) if year else current_year

        return build_date_range(year, month, d1, d2)

    return None


def extract_time_range(query: str):

    if isinstance(query, tuple):
        return query 
    
    if not isinstance(query, str):
        return None

    # -----------------------------
    # STEP 1: RELATIVE TIME
    # -----------------------------
    relative = extract_relative_time(query)
    if relative:
        return relative

    # -----------------------------
    # STEP 2: RANGE (MOVE UP)
    # -----------------------------
    query = normalize_time_expression(query)

    range_result = extract_range_date(query)
    if range_result:
        return range_result

    # -----------------------------
    # STEP 3: SINGLE DATE (LAST)
    # -----------------------------
    single = extract_single_date(query)
    if single:
        return single

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



def parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S.%fZ",  # 2026-04-28T10:14:34.000Z
        "%Y-%m-%dT%H:%M:%SZ",     # 2026-04-28T10:14:34Z
        "%Y-%m-%d %H:%M:%S"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def parse_any_datetime(value: str) -> Optional[datetime]:
    try:
        if "T" in value:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.strptime(value, "%Y-%m-%d")
    except Exception:
        return None


def format_time_generate(time_range: Union[str, Tuple[str, str]]) -> str:
    if not time_range:
        return ""

    try:
        # -----------------------------
        # CASE 1: Single value
        # -----------------------------
        if isinstance(time_range, str):
            dt = parse_any_datetime(time_range)

            if not dt:   # ✅ CRITICAL FIX
                return ""

            return dt.strftime("%B %d").replace(" 0", " ")

        # -----------------------------
        # CASE 2: Tuple
        # -----------------------------
        if isinstance(time_range, tuple):
            start, end = time_range

            start_dt = parse_any_datetime(start) if start else None
            end_dt = parse_any_datetime(end) if end else None

            # ✅ FIX: Guard before usage
            if not start_dt:
                return ""

            start_fmt = start_dt.strftime("%B %d").replace(" 0", " ")

            # Only start exists
            if not end_dt:
                return start_fmt

            # Same day
            if start_dt.date() == end_dt.date():
                return start_fmt

            end_fmt = end_dt.strftime("%B %d").replace(" 0", " ")

            return f"{start_fmt} to {end_fmt}"

    except Exception:
        return ""

    return ""