from typing import Any


INVALID_VALUES = {
    None,
    "",
    " ",
    "NA",
    "N/A",
    "null",
    "None",
    "unknown",
    "-",
}


def clean_value(value: Any):

    # -----------------------------------------
    # STRING CLEANING
    # -----------------------------------------

    if isinstance(value, str):
        value = value.strip()

    # -----------------------------------------
    # DICT SPECIAL CASE
    # -----------------------------------------

    if isinstance(value, dict):

        text = value.get("text")

        if text in INVALID_VALUES:
            return None

        return value

    # -----------------------------------------
    # NORMAL VALUES
    # -----------------------------------------

    if value in INVALID_VALUES:
        return None

    return value


def has_value(value: Any) -> bool:

    return clean_value(value) is not None


def safe_float(
    value: Any,
    default: float = 0.0
) -> float:

    if value is None:
        return default

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return default

        invalid_values = {
            "N/A",
            "NA",
            "NULL",
            "NONE",
            "--",
            "-",
            "UNKNOWN"
        }

        if value.upper() in invalid_values:
            return default

        try:
            return float(value)

        except ValueError:
            return default

    return default