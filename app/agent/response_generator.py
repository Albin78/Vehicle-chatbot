from app.llm.ollama_client import OllamaClient
from app.utils.logger import logger
from datetime import datetime

llm = OllamaClient()


from datetime import datetime
from typing import Union, Tuple

def format_time_range(time_range: Union[str, Tuple[str, str]]) -> str:
    if not time_range:
        return ""

    try:
        # -----------------------------
        # CASE 1: Single date string
        # -----------------------------
        if isinstance(time_range, str):
            dt = datetime.strptime(time_range, "%Y-%m-%d")
            return dt.strftime("%B %d").replace(" 0", " ")

        # -----------------------------
        # CASE 2: Tuple (range)
        # -----------------------------
        if isinstance(time_range, tuple):
            start, end = time_range

            if not start:
                return ""

            start_date = datetime.strptime(start, "%Y-%m-%d")

            # If end is missing → treat as single
            if not end:
                return start_date.strftime("%B %d").replace(" 0", " ")

            end_date = datetime.strptime(end, "%Y-%m-%d")

            # Same date → single output
            if start_date == end_date:
                return start_date.strftime("%B %d").replace(" 0", " ")

            # Range output
            start_fmt = start_date.strftime("%B %d").replace(" 0", " ")
            end_fmt = end_date.strftime("%B %d").replace(" 0", " ")

            return f"{start_fmt} to {end_fmt}"

    except Exception:
        return ""

    return ""


def get_unit(metric):
    unit_map = {
        "speed": "km/h",
        "distance": "km",
        "battery": "mV",
        "temperature": "°C"
    }
    return unit_map.get(metric, "")



def build_user_message(result, intent):

    if not result or "error" in result:
        return result.get("error", "I couldn't find any data for the given vehicle.")

    time_context = ""
    if intent.time_range:
        timestamp_to_date = format_time_range(intent.time_range)
        time_context = f" for the time range {timestamp_to_date}"

    result_type = result.get("type")

    # -----------------------------
    # REALTIME METRIC
    # -----------------------------
    if result_type == "realtime_metric":
        metric = result.get("metric")
        value = result.get("value")

        unit = get_unit(metric)

        return (
            f"The current {metric} of vehicle {result.get('vehicle')} "
            f"is {value} {unit}."
        ) 
    
    if result_type == "alert_summary":

        latest = result.get("latest_alert", {})

        parts = []

        parts.append(
            f"The latest {latest.get('alert_name')} alert"
        )

        if latest.get("time"):
            time = latest.get('Date')
            time = format_time_range(time)
            logger.info(f"Changed time format using custom function: {time}")
            parts.append(f"occurred at {time}")

        if latest.get("driver"):
            parts.append(f"with driver {latest.get('driver')}")

        if latest.get("current_value"):
            parts.append(f"value was {latest.get('current_value')}")

        if latest.get("duration"):
            parts.append(f"lasting {latest.get('duration')}")

        if result.get("total_alerts") is not None:
            parts.append(f"total alerts are {result.get('total_alerts')}")
        return ", ".join(parts) + "."


    if result_type == "realtime_status":

        parts = []

        parts.append(
            f"The vehicle {result.get('vehicle')} is {result.get('status')}"
        )

        if result.get("last_updated"):
            parts.append(f"(last updated {result.get('last_updated')})")

        # dynamic fields
        if "speed" in result:
            parts.append(f"speed is {result['speed']} km/h")

        if "battery_level" in result:
            parts.append(f"battery is {result['battery_level']} V")

        if "fuel_capacity" in result:
            parts.append(f"fuel capacity is {result['fuel_capacity']} L")

        if "tanker_fuel_capacity" in result:
            parts.append(f"tanker capacity is {result['tanker_fuel_capacity']} L")

        if "weight" in result:
            parts.append(f"weight is {result['weight']} kg")

        if "driver" in result:
            parts.append(f"driver is {result['driver']}")

        return ", ".join(parts) + "."
    
    
    # HISTORICAL METRIC
    # -----------------------------
    if result_type == "metric":
        value = result.get("value")

        if value is None:
            return "I couldn't find data for the requested metric."

        unit = get_unit(intent.metric)

        if intent.aggregation:
            return (
                f"For vehicle {intent.vehicle_id}, the {intent.metric} "
                f"{intent.aggregation}{time_context} is {value} {unit}."
            )
        else:
            return (
                f"For vehicle {intent.vehicle_id}, the current "
                f"{intent.metric}{time_context} is {value} {unit}."
            )

    # -----------------------------
    # SUMMARY
    # -----------------------------
    if result_type == "summary":
        return (
            f"Vehicle {intent.vehicle_id}{time_context} traveled "
            f"{result.get('total_distance')} km with an average speed of "
            f"{result.get('average_speed')} km/h and engine hours "
            f"{result.get('engine_hours')}."
        )

    return result["message"]



def generate_response(result, intent):

    if not result or "error" in result:
        return result.get("error", "No data found.")

    base_message = build_user_message(result, intent)

   
    prompt = f"""
You are a strict response formatter.

Rewrite the sentence ONLY for grammar and readability.

----------------------------------------
INPUT:
{base_message}
----------------------------------------

CRITICAL RULES:

- You MUST NOT remove ANY information
- You MUST NOT shorten the sentence
- You MUST include EVERY field mentioned
- You MUST keep ALL numbers EXACT
- You MUST keep ALL units EXACT
- Output must contain SAME number of data points as input
- Do NOT summarize

----------------------------------------

Return EXACTLY one sentence.
"""

    return llm.generate(prompt)