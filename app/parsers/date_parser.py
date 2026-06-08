import re
import calendar

from datetime import (
    datetime,
    timedelta,
    timezone
)

from typing import (
    Union,
    Tuple,
    Optional
)


# =========================================================
# CONSTANTS
# =========================================================

MONTH_MAP = {

    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12
}


DATE_CONNECTORS = r"(?:to|through|until|till|-)"


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_time_expression(query: str) -> str:

    query = query.lower()

    # Remove filler words
    query = re.sub(r"\bbetween\b", "", query)
    query = re.sub(r"\bfrom\b", "", query)

    # Normalize shorthand
    query = re.sub(r"\blst\b", "last", query)

    # Normalize connectors
    query = re.sub(
        r"\b(?:through|until|till)\b",
        "to",
        query
    )

    # Normalize dash ranges
    query = re.sub(
        r"\s*-\s*",
        " to ",
        query
    )

    # Remove ordinal suffixes
    query = re.sub(
        r"(\d+)(st|nd|rd|th)",
        r"\1",
        query
    )

    # Collapse spaces
    query = re.sub(
        r"\s+",
        " ",
        query
    )

    return query.strip()


# =========================================================
# VALIDATION
# =========================================================

def validate_day(
    year: int,
    month: int,
    day: int
) -> int:

    max_day = calendar.monthrange(
        year,
        month
    )[1]

    if day < 1:
        return 1

    if day > max_day:
        return max_day

    return day


def adjust_future_date(dt: datetime) -> datetime:

    today = datetime.now(
        timezone.utc
    ).date()

    # If parsed date is in future,
    # assume previous year
    if dt.date() > today:
        dt = dt.replace(
            year=dt.year - 1
        )

    return dt


# =========================================================
# BUILDERS
# =========================================================

def build_date(
    year: int,
    month: int,
    day: int
) -> datetime:

    day = validate_day(
        year,
        month,
        day
    )

    dt = datetime(
        year,
        month,
        day
    )

    return adjust_future_date(dt)


def build_date_range(
    year,
    month,
    d1,
    d2
):

    month_num = MONTH_MAP[
        month[:3]
    ]

    year = int(year)

    d1 = int(d1)
    d2 = int(d2)

    d1 = validate_day(
        year,
        month_num,
        d1
    )

    d2 = validate_day(
        year,
        month_num,
        d2
    )

    if d1 > d2:
        d1, d2 = d2, d1

    start = build_date(
        year,
        month_num,
        d1
    )

    end = build_date(
        year,
        month_num,
        d2
    )

    return (
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d")
    )


# =========================================================
# QUERY CHECK
# =========================================================

def is_time_range_in_query(
    query: str
) -> bool:

    query = query.lower()

    patterns = [

        r"\b(today|yesterday)\b",
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",

        r"\blast\s+\d+\s+days\b",
        r"\blst\s+\d+\s+days\b",

        r"\bthis\s+week\b",
        r"\blast\s+week\b",

        r"\bthis\s+month\b",
        r"\blast\s+month\b",

        r"\bjan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec\b",

        r"\d{4}-\d{2}-\d{2}",

        r"\d{1,2}/\d{1,2}/\d{2,4}"
    ]

    return any(
        re.search(p, query)
        for p in patterns
    )


# =========================================================
# RELATIVE TIME
# =========================================================

def extract_relative_time(
    query: str
):

    query = query.lower()

    today = datetime.now(
        timezone.utc
    ).date()

    # -----------------------------------------
    # TODAY
    # -----------------------------------------

    if re.search(r"\btoday\b", query):

        return (
            str(today),
            str(today)
        )

    # -----------------------------------------
    # YESTERDAY
    # -----------------------------------------

    if re.search(r"\byesterday\b", query):

        y = today - timedelta(days=1)

        return (
            str(y),
            str(y)
        )

    # -----------------------------------------
    # LAST N DAYS
    # -----------------------------------------

    match = re.search(
        r"last\s+(\d+)\s+days",
        query
    )

    if match:

        days = int(
            match.group(1)
        )

        start = today - timedelta(days=days)

        return (
            str(start),
            str(today)
        )

    # -----------------------------------------
    # THIS WEEK
    # -----------------------------------------

    if "this week" in query:

        start = today - timedelta(
            days=today.weekday()
        )

        return (
            str(start),
            str(today)
        )

    # -----------------------------------------
    # LAST WEEK
    # -----------------------------------------

    if "last week" in query:

        start = today - timedelta(
            days=today.weekday() + 7
        )

        end = start + timedelta(days=6)

        return (
            str(start),
            str(end)
        )

    # -----------------------------------------
    # THIS MONTH
    # -----------------------------------------

    if "this month" in query:

        start = today.replace(day=1)

        return (
            str(start),
            str(today)
        )

    # -----------------------------------------
    # LAST MONTH
    # -----------------------------------------

    if "last month" in query:

        first_this_month = today.replace(day=1)

        last_month_end = (
            first_this_month - timedelta(days=1)
        )

        last_month_start = (
            last_month_end.replace(day=1)
        )

        return (
            str(last_month_start),
            str(last_month_end)
        )

    # -----------------------------------------
    # WEEKDAYS
    # -----------------------------------------

    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    for wd_str, wd_idx in weekdays.items():
        if re.search(rf"\b{wd_str}\b", query):
            days_ago = (today.weekday() - wd_idx) % 7
            target_date = today - timedelta(days=days_ago)
            return (
                str(target_date),
                str(target_date)
            )

    return None


# =========================================================
# EXPLICIT SINGLE DATE
# =========================================================

def extract_single_date(
    query: str
):

    query = query.lower()

    current_year = datetime.now(
        timezone.utc
    ).year

    # -----------------------------------------
    # APRIL 10
    # -----------------------------------------

    pattern = re.search(

        r"(?:on\s+)?"
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        r"[a-z]*\s+"
        r"(\d{1,2})"
        r"(?:\s+(\d{4}))?",

        query
    )

    if pattern:

        month, day, year = pattern.groups()

        year = int(year) if year else current_year

        month_num = MONTH_MAP[
            month[:3]
        ]

        dt = build_date(
            year,
            month_num,
            int(day)
        )

        date_str = dt.strftime("%Y-%m-%d")

        return (
            date_str,
            date_str
        )

    # -----------------------------------------
    # YYYY-MM-DD
    # -----------------------------------------

    iso_pattern = re.search(
        r"(\d{4})-(\d{2})-(\d{2})",
        query
    )

    if iso_pattern:

        year, month, day = map(
            int,
            iso_pattern.groups()
        )

        dt = build_date(
            year,
            month,
            day
        )

        date_str = dt.strftime("%Y-%m-%d")

        return (
            date_str,
            date_str
        )

    return None


# =========================================================
# RANGE DATES
# =========================================================

def extract_range_date(
    query: str
):

    current_year = datetime.now(
        timezone.utc
    ).year

    # -----------------------------------------
    # APRIL 10 TO APRIL 25
    # -----------------------------------------

    pattern_full = re.search(

        rf"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        rf"[a-z]*\s+(\d{{1,2}})\s+"
        rf"{DATE_CONNECTORS}\s+"
        rf"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        rf"[a-z]*\s+(\d{{1,2}})"
        rf"(?:\s+(\d{{4}}))?",

        query
    )

    if pattern_full:

        m1, d1, m2, d2, year = (
            pattern_full.groups()
        )

        year = int(year) if year else current_year

        start = build_date(
            year,
            MONTH_MAP[m1[:3]],
            int(d1)
        )

        end = build_date(
            year,
            MONTH_MAP[m2[:3]],
            int(d2)
        )

        return (
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d")
        )

    # -----------------------------------------
    # APRIL 10 TO 25
    # -----------------------------------------

    pattern_same_month = re.search(

        rf"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        rf"[a-z]*\s+"
        rf"(\d{{1,2}})\s+"
        rf"{DATE_CONNECTORS}\s+"
        rf"(\d{{1,2}})"
        rf"(?:\s+(\d{{4}}))?",

        query
    )

    if pattern_same_month:

        month, d1, d2, year = (
            pattern_same_month.groups()
        )

        year = int(year) if year else current_year

        return build_date_range(
            year,
            month,
            d1,
            d2
        )

    return None


# =========================================================
# MAIN EXTRACTOR
# =========================================================

def extract_time_range(
    query
):

    if isinstance(query, tuple):
        return query

    if not isinstance(query, str):
        return None

    query = normalize_time_expression(query)

    # -----------------------------------------
    # PRIORITY 1:
    # EXPLICIT RANGE
    # -----------------------------------------

    range_result = extract_range_date(query)

    if range_result:
        return range_result

    # -----------------------------------------
    # PRIORITY 2:
    # EXPLICIT SINGLE DATE
    # -----------------------------------------

    single_result = extract_single_date(query)

    if single_result:
        return single_result

    # -----------------------------------------
    # PRIORITY 3:
    # RELATIVE DATES
    # -----------------------------------------

    relative_result = extract_relative_time(query)

    if relative_result:
        return relative_result

    return None


# =========================================================
# GENERIC DATETIME PARSER
# =========================================================

def parse_date(
    date_str: str
) -> Optional[datetime]:

    if not date_str:
        return None

    formats = [

        "%Y-%m-%d",

        "%Y-%m-%dT%H:%M:%S.%fZ",

        "%Y-%m-%dT%H:%M:%SZ",

        "%Y-%m-%d %H:%M:%S"
    ]

    for fmt in formats:

        try:
            return datetime.strptime(
                date_str,
                fmt
            )

        except ValueError:
            continue

    return None


def parse_any_datetime(
    value: str
) -> Optional[datetime]:

    try:

        if "T" in value:

            return datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00"
                )
            )

        return datetime.strptime(
            value,
            "%Y-%m-%d"
        )

    except Exception:
        return None


# =========================================================
# FORMATTERS
# =========================================================

def format_time_range(
    time_range
):

    if not time_range:
        return ""

    if isinstance(time_range, tuple):

        start, end = time_range

        try:

            start_dt = datetime.strptime(
                start,
                "%Y-%m-%d"
            )

            end_dt = datetime.strptime(
                end,
                "%Y-%m-%d"
            )

            return (
                f"{start_dt.strftime('%B %d')} "
                f"to "
                f"{end_dt.strftime('%B %d')}"
            )

        except Exception:
            return str(time_range)

    return str(time_range)


def format_time_generate(
    time_range: Union[
        str,
        Tuple[str, str]
    ]
) -> str:

    if not time_range:
        return ""

    try:

        # -----------------------------------------
        # SINGLE VALUE
        # -----------------------------------------

        if isinstance(time_range, str):

            dt = parse_any_datetime(
                time_range
            )

            if not dt:
                return ""

            return dt.strftime(
                "%B %d"
            ).replace(" 0", " ")

        # -----------------------------------------
        # RANGE
        # -----------------------------------------

        if isinstance(time_range, tuple):

            start, end = time_range

            start_dt = (
                parse_any_datetime(start)
                if start else None
            )

            end_dt = (
                parse_any_datetime(end)
                if end else None
            )

            if not start_dt:
                return ""

            start_fmt = start_dt.strftime(
                "%B %d"
            ).replace(" 0", " ")

            if not end_dt:
                return start_fmt

            if start_dt.date() == end_dt.date():
                return start_fmt

            end_fmt = end_dt.strftime(
                "%B %d"
            ).replace(" 0", " ")

            return (
                f"{start_fmt} "
                f"to "
                f"{end_fmt}"
            )

    except Exception:
        return ""

    return ""