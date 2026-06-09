from app.llm.ollama_client import OllamaClient
from app.schemas.intent_schema import QueryIntent
from app.utils.logger import logger

from app.validators.intent_validator import sanitize_llm_output
from app.validators.operation_validators import post_validate

from app.parsers.date_parser import extract_time_range


llm = OllamaClient()


# =========================================================
# DEFAULT FALLBACK
# =========================================================

DEFAULT_INTENT = {
    "action": "fetch",
    "vehicle_id": None,
    "source": None,
    "metrics": [],
    "aggregation": None,
    "alert_analysis": None,
    "time_range": None,
    "summary_requested": False
}


# =========================================================
# INTENT EXTRACTION
# =========================================================

def extract_intent(query: str) -> QueryIntent:

    # -----------------------------------------------------
    # EXTRACT TIME RANGE FIRST
    # -----------------------------------------------------

    parsed_time_range = extract_time_range(query)

    # -----------------------------------------------------
    # LLM PROMPT
    # -----------------------------------------------------

    prompt = f"""
You are an expert intent classifier for a Vehicle Monitoring System.

Return ONLY valid JSON.
Do NOT explain anything.

=========================================================
SUPPORTED SOURCES
=========================================================

1. latest
   - current data
   - latest status
   - live vehicle information

2. summary
   - historical analytics
   - aggregated metrics
   - date-range operations

3. alert
   - overspeed
   - violations
   - alert history

=========================================================
SUPPORTED METRICS
=========================================================

speed
fuel_level
fuel_capacity
battery
weight
mileage
temperature
ignition
battery_voltage
engine_temperature
engine_rpm
fuel_percentage
tanker_fuel_percentage
door_status
seatbelt_status
engine_hours
idle_time
distance
fuel_consumed
wasl_identity_number

=========================================================
RULES
=========================================================

1. If query asks:
   - current
   - latest
   - now
   - status

THEN:
source = "latest"

---------------------------------------------------------

2. If query contains:
   - time range
   - average
   - minimum
   - maximum
   - summary
   - report

THEN:
source = "summary"

---------------------------------------------------------

3. If query contains:
   - alert
   - overspeed
   - violation
   - idling

THEN:
source = "alert"

---------------------------------------------------------

4. Extract ONLY metrics explicitly mentioned.

5. metrics MUST be ARRAY.

6. aggregation allowed:
- minimum
- maximum
- average

7. alert_analysis allowed:
- latest
- count
- summary

8. summary_requested = true
ONLY if query asks:
- full status
- complete status
- current status
- latest status

9. vehicle_id
MUST extract the vehicle identifier if present in the text (e.g. '1832 RXB', '2376 ABC', '73 RRR'). Do NOT extract generic words like 'truck' or 'car' as vehicle_id.

=========================================================
STRICT OUTPUT FORMAT
=========================================================

{{
  "action": "fetch",
  "vehicle_id": string | null,
  "source": "latest" | "summary" | "alert" | null,
  "metrics": [],
  "aggregation": "minimum" | "maximum" | "average" | null,
  "alert_analysis": "latest" | "count" | "summary" | null,
  "time_range": null,
  "summary_requested": true | false
}}

=========================================================
INPUT

{query}

OUTPUT
=========================================================

JSON only
"""

    # -----------------------------------------------------
    # LLM GENERATION
    # -----------------------------------------------------

    raw_response = llm.generate(prompt)
    
    logger.info(f"Query input: {query}")
    logger.info(f"Raw LLM Response: {raw_response}")

    # -----------------------------------------------------
    # SANITIZE
    # -----------------------------------------------------

    clean_data = sanitize_llm_output(raw_response)

    logger.info(f"Sanitized Intent: {clean_data}")

    # -----------------------------------------------------
    # TIME RANGE INJECTION
    # -----------------------------------------------------

    if parsed_time_range:
        clean_data["time_range"] = parsed_time_range

    # -----------------------------------------------------
    # POST VALIDATION
    # -----------------------------------------------------

    clean_data = post_validate(
        clean_data=clean_data,
        query=query
    )

    logger.info(f"Post Validated Intent: {clean_data}")

    try:

        intent = QueryIntent(**clean_data)

    except Exception as e:

        logger.error(
            f"Pydantic validation failed: {e}",
            exc_info=True
        )

        intent = QueryIntent(**DEFAULT_INTENT)

    # -----------------------------------------------------
    # FINAL LOGGING
    # -----------------------------------------------------

    logger.info(f"Final Intent Object: {intent}")
    logger.info(f"Intent Type: {type(intent)}")
    logger.info(f"Vehicle id extracted: {intent.vehicle_id}")

    return intent