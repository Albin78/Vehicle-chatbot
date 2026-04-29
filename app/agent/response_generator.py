from app.llm.ollama_client import OllamaClient
from datetime import datetime
from app.parsers.date_parser import format_time_generate
from app.utils.logger import logger

llm = OllamaClient()



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
        timestamp_to_date = format_time_generate(intent.time_range)
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
    
    if result_type == "alert_latest":

        parts = []

        parts.append(
            f"The latest {result.get('alert_name')} alert"
        )

        if result.get("time"):
            formatted_time = format_time_generate(result.get("time"))
            parts.append(f"occurred on {formatted_time}")

        if result.get("driver"):
            parts.append(f"with driver {result.get('driver')}")

        if result.get("value"):
            parts.append(f"recorded a value of {result.get('value')}")

        if result.get("duration"):
            parts.append(f"lasting {result.get('duration')}")

        return ", ".join(parts) + "."
    

    
    if result_type == "alert_count":

        total = result.get("total_alerts", 0)

        return f"A total of {total} alerts were recorded for the given vehicle in the selected time range."
    

    
    if result_type == "alert_summary":

        latest = result.get("latest_alert", {})
        peak = result.get("peak_alert", {})

        parts = []

        # Total alerts
        if result.get("total_alerts") is not None:
            parts.append(f"A total of {result.get('total_alerts')} alerts were recorded")

        # Most common alert
        if result.get("most_common_alert"):
            parts.append(f"with {result.get('most_common_alert')} being the most frequent")

        # Latest alert
        if latest:
            latest_parts = []

            latest_parts.append(f"the most recent alert was {latest.get('alert_name')}")

            if latest.get("time"):
                formatted_time = format_time_generate(latest.get("time"))
                logger.info(f"The timestamp taken from alert api data: {latest.get('time')} and Converted timestamp to str: {formatted_time}")
                latest_parts.append(f"on {formatted_time}")

            if latest.get("driver"):
                latest_parts.append(f"by driver {latest.get('driver')}")

            if latest.get("current_value"):
                latest_parts.append(f"with a value of {latest.get('current_value')}")

            if latest.get("duration"):
                latest_parts.append(f"lasting {latest.get('duration')}")

            parts.append(" ".join(latest_parts))

        # Peak alert
        if peak:
            peak_parts = []

            peak_parts.append(f"the highest severity alert recorded was {peak.get('alert_name')}")

            if peak.get("value"):
                peak_parts.append(f"with a value of {peak.get('value')}")

            if peak.get("time"):
                formatted_time = format_time_generate(peak.get("time"))
                peak_parts.append(f"on {formatted_time}")

            parts.append(" ".join(peak_parts))

        return ". ".join(parts) + "."
    


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

        if "weight" in result and result["weight"] is not None:
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
            f"{result.get('average_speed')} km/h, total moving time of {result.get('total_moving_time')} "
            f" total idl time {result.get('total_idle_time')} and engine hours "
            f"{result.get('engine_hours')}."
        )

    return result["message"]



def generate_response(result, intent):

    if not result or "error" in result:
        return result.get("error", "No data found.")

    base_message = build_user_message(result, intent)

   
    prompt = f"""
You are a strict response formatter.

Your task is to rewrite the sentence ONLY for grammar and readability.

----------------------------------------
INPUT:
{base_message}
----------------------------------------

STRICT RULES (MANDATORY):

- Output EXACTLY one sentence
- Do NOT add any explanation
- Do NOT include phrases like "Here is the rewritten version"
- Do NOT add new information
- Do NOT infer or summarize anything
- Do NOT remove any information
- Preserve ALL values, numbers, units, and names EXACTLY
- Preserve ALL data points present in the input
- Only fix grammar and sentence flow

----------------------------------------

OUTPUT:
"""

    return llm.generate(prompt)