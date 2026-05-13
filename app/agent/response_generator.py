from app.llm.ollama_client import OllamaClient
from app.parsers.date_parser import format_time_generate
from app.utils.logger import logger
import re
from app.response_generator.formatt_router import build_user_message


llm = OllamaClient()



def clean_driver_name(driver: str | None) -> str | None:
    if not driver:
        return driver

    # Remove anything inside parentheses
    return re.sub(r"\s*\(.*?\)", "", driver).strip()

def get_unit(metric):
    unit_map = {
        "speed": "km/h",
        "distance": "km",
        "battery": "mV",
        "temperature": "°C"
    }
    return unit_map.get(metric, "")


def metric_not_available_response(metric: str, vehicle: str) -> str:
    suggestions = {
        "weight": "You can check speed, battery status, or fuel details instead.",
        "battery": "You can check speed or fuel details instead.",
        "speed": "You can check battery or fuel details instead.",
        "fuel_level": "You can check battery or fuel details instead."
    }

    suggestion_text = suggestions.get(metric, "Try asking for other vehicle details.")

    return (
        f"I couldn't find the current {metric} data for vehicle {vehicle}. "
        f"{suggestion_text}"
    )


def build_user_messages(result, intent):

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
        metric = result.get("metric") or intent.metric or "data"
        value = result.get("value")
        vehicle = result.get("vehicle")

        # 🚨 CRITICAL FIX
        if value is None:
            return metric_not_available_response(metric, vehicle)

        unit = get_unit(metric)

        return (
            f"The current {metric} of vehicle {vehicle} "
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
        
        if result.get("limit"):
            parts.append(f"allowed speed limit is {result.get('limit')}")

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
            
            if latest.get("limit") is not None:
                latest_parts.append(f"while allowed speed limit is {latest.get('limit')}")

            if latest.get("duration"):
                latest_parts.append(f"lasting {latest.get('duration')}")

            parts.append(" ".join(latest_parts))

        # Peak alert
        if peak:
            peak_parts = []

            peak_parts.append(f"the highest severity alert recorded was {peak.get('alert_name')}")

            if peak.get("value"):
                peak_parts.append(f"with a value of {peak.get('value')}")
            
            if peak.get("limit") is not None:
                peak_parts.append(f"while allowed speed limit is {peak.get('limit')}")

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

        # if result.get("last_updated"):
        #     parts.append(f"(last updated {result.get('last_updated')})")

        # dynamic fields
        if "speed" in result:
            parts.append(f"speed is {result['speed']} km/h")

        if "battery_level" in result:
            parts.append(f"battery is {result['battery_level']} V")

        if "fuel_capacity" in result:
            parts.append(f"fuel capacity is {result['fuel_capacity']} L")

        if "tanker_fuel_capacity" in result:
            parts.append(f"tanker capacity is {result['tanker_fuel_capacity']} L")
        
        if "fuellitre" in result and "fuelLevel" in result:
            if result["fuelLevel"] and result["fuellitre"]:
                parts.append(f"fuel level is {result['fuelLevel']} and fuel level in litres is {result['fuellitre']} litres")

        if "weight" in result:
            if result["weight"] is not None:
                parts.append(f"weight is {result['weight']} kg")
            else:
                parts.append("weight data is currently unavailable.")

        if "driver" in result:
            driver_clean = clean_driver_name(result["driver"])
            parts.append(f"driver is {driver_clean}")

        return ", ".join(parts) + "."
    
    
    # HISTORICAL METRIC
    # -----------------------------
    if result_type == "metric":
        value = result.get("value")
        metric = result.get("metric") or intent.metric or "data"

        if value is None:
            return metric_not_available_response(metric, result.get("vehicle"))

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
            f"Vehicle {intent.vehicle_id} of type {result.get('vehicle_type')} belongs to group {result.get('group')} "
            f"for time range {time_context} traveled {result.get('total_distance')} km "
            f"with an average speed of {result.get('average_speed')} km/h, "
            f"total moving time of {result.get('total_moving_time')}, "
            f"total idle time {result.get('total_idle_time')} and engine hours "
            f"{result.get('engine_hours')} and stop time {result.get('total_stop_time')}."
        )

    return result["message"]



def generate_response(result, intent):

    if not result or "error" in result:
        return result.get("error", "No data found.")

    base_message = build_user_message(result, intent)

   
    prompt = f"""
You are a production chatbot response formatter.

Your job is to convert the given system-generated response into a natural, conversational reply suitable for an end user.

----------------------------------------
INPUT:
{base_message}
----------------------------------------

CRITICAL RULES (NON-NEGOTIABLE):

- Do NOT change any numbers, values, units, names, or facts
- Do NOT remove any information
- Do NOT add any new information
- Do NOT infer or calculate anything

- Every piece of information in INPUT must appear in OUTPUT

----------------------------------------

CONVERSATION STYLE RULES:

- Write like a real assistant speaking to a user
- Do NOT use section headers like:
  "Metrics", "Time Breakdown", "Info"

- Present information naturally in sentences
- Use 2–4 short sentences (NOT bullet points)
- Keep it smooth and easy to read

- Avoid robotic chaining of commas
- Avoid overly long sentences

----------------------------------------

STRUCTURE GUIDELINE:

- Start with vehicle identity
- Then mention time range if specified
- Then summarize key metrics (distance, speed)
- Then include time breakdown (moving, idle, engine, stop)

----------------------------------------

TONE:

- Professional and natural
- Slightly conversational
- NOT overly friendly, NOT robotic

----------------------------------------

OUTPUT RULES:

- Return ONLY the final response
- No meta-text
- No labels
- No formatting like lists or sections

----------------------------------------

OUTPUT:
"""
    
    
    return llm.generate(prompt)