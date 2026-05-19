# app/utils/value_cleaner.py

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


def clean_value(value):

    if isinstance(value, str):
        value = value.strip()
    
    if isinstance(value, dict):
        if value.get("text") in INVALID_VALUES:
            return None
        
        
    if not isinstance(value, dict) and value in INVALID_VALUES:
        return None

    return value


def has_value(value):

    return clean_value(value) is not None


def safe_float(value, default=0.0):

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

    except (ValueError, TypeError):
        return default