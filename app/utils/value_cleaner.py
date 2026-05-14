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