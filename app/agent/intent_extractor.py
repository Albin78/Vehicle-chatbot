from app.llm.ollama_client import OllamaClient
from app.db.mongoclient import get_db_fields
from app.schemas.intent_schema import QueryIntent
from app.utils.logger import logger
from app.validators.intent_validators import sanitize_llm_output, post_validate, map_service
from app.parsers.date_parser import extract_time_range

llm = OllamaClient()


# --------------------------------------------------
# DEFAULT SAFE INTENT (FALLBACK)
# --------------------------------------------------
DEFAULT_INTENT = {
    "action": "fetch",
    "vehicle_id": None,
    "metric": None,
    "aggregation": None,
    "analysis": None,
    "time_range": None,
    "intent_type": None,  
    "service": None
}


# INTENT EXTRACTION
def extract_intent(query: str) -> QueryIntent:

    fields = get_db_fields()

    prompt = f"""
You are an expert intent classifier for a Vehicle Monitoring System.

Return ONLY ONE valid JSON.

----------------------------------------
STEP 1: RELEVANCE CHECK

If NOT vehicle-related → return all null

----------------------------------------
STEP 2: INTENT CLASSIFICATION (CRITICAL)

Classify query into ONE of:

1. "realtime"  
   → current / latest / now / status  
   → NO time_range required  

2. "historical"  
   → contains time range  
   → analytics / summary  

3. "alert"  
   → contains words like:
     "overspeed", "alerts", "violations"

4. "telemetry"  
   → raw metric without time range  
   → from DB

----------------------------------------
STEP 3: FIELD EXTRACTION

Extract:
- vehicle_id
- metric (ONLY if exact word exists)
- aggregation (ONLY if explicitly present)
- time_range (ONLY if explicitly present)

----------------------------------------
STRICT OUTPUT FORMAT:

{{
  "action": "fetch | update | delete",
  "vehicle_id": string | null,
  "metric": string | null,
  "aggregation": "minimum" | "maximum" | "average" | null,
  "analysis": string | null,
  "time_range": string | null,
  "intent_type": "realtime | historical | alert | telemetry | null",
  "service": null
}}

----------------------------------------
RULES:

- DO NOT guess
- DO NOT infer metric
- DO NOT add fields
- DO NOT explain

----------------------------------------
INPUT:
{query}

----------------------------------------
OUTPUT:
JSON only
"""

    raw_response = llm.generate(prompt,)

    logger.info(f"Raw LLM Response: {raw_response}")

    # -----------------------------
    # SANITIZE OUTPUT
    # -----------------------------
    clean_data = sanitize_llm_output(raw_response)
    clean_data = post_validate(clean_data, query, fields)
    clean_data = map_service(clean_data)

    logger.info(f"After post validation JSON: {clean_data}")
    
    time_range = extract_time_range(query)

    if time_range:
        clean_data["time_range"] = time_range
    else:
        clean_data["time_range"] = None
    # -----------------------------
    # FINAL INTENT OBJECT
    # -----------------------------
    try:
        intent = QueryIntent(**clean_data)
    except Exception as e:
        logger.error(f"Pydantic validation failed: {e}")
        intent = QueryIntent(**DEFAULT_INTENT)

    logger.info(f"Final Intent: {intent}")
    logger.info(f"Type of intent: {type(intent)}")

    return intent