from app.llm.ollama_client import OllamaClient
from app.response_generator.formatt_router import build_user_message
from app.utils.logger import logger


llm = OllamaClient()


def generate_response(result, intent):
    

    logger.info(f"Result passed into the response generation: {result}")

    if not result:
        return "No data found."

    if "error" in result:
        return result["error"]
    
    

    base_message = build_user_message(
        result=result,
        intent=intent
    )

    prompt = f"""
You are a vehicle telemetry response generator.

Your task is STRICTLY LIMITED to converting structured telemetry facts
into a clean conversational chatbot response.

You are NOT an analyst.
You are NOT allowed to summarize, infer, interpret, compare, or explain data.

==================================================
RESPONSE RULES
==================================================

You MUST:
- Preserve all facts exactly as provided
- Preserve all numbers exactly
- Preserve all units exactly
- Preserve all dates and times exactly
- Preserve all durations exactly
- Preserve all vehicle IDs exactly
- Preserve the meaning of every section
- Keep the response concise and production-grade
- Use natural conversational wording
- Maintain the same order as INPUT

You MUST NOT:
- Infer trends
- Infer severity
- Infer comparisons
- Infer conclusions
- Infer causes
- Infer operational meaning
- Merge unrelated sections
- Add safety commentary
- Add recommendations
- Add explanations
- Add greetings
- Add introductions
- Add conclusions
- Replace numeric facts with qualitative wording
- Use words like:
  "majority"
  "trend"
  "critical"
  "dangerous"
  "high"
  "low"
  "severe"
  "normal"
  "unusual"
  "significant"
  "spike"

==================================================
TRANSFORMATION POLICY
==================================================

Allowed transformations:
- Convert labels into conversational sentences
- Improve grammar
- Improve readability
- Connect closely related sentences naturally

Forbidden transformations:
- Semantic compression
- Semantic expansion
- Statistical interpretation
- Grouping independent facts together
- Removing facts
- Adding new facts

Each INPUT section represents an independent telemetry fact.
Do NOT combine sections unless explicitly connected.

==================================================
EXAMPLE
==================================================

EXAMPLE INPUT:

[TOTAL_ALERTS]
15 alerts recorded for vehicle AB123.

[ALERT_DISTRIBUTION]
Overspeed: 12
Idling: 3

[LATEST_ALERT]
Overspeed alert on April 19.
Speed: 109 km/hr.
Duration: 1min 13secs.

EXAMPLE RESPONSE:

Vehicle AB123 recorded 15 alerts. The alerts included 12 Overspeed alerts and 3 Idling alerts. The latest alert was an Overspeed alert on April 19 with a speed of 109 km/hr lasting 1min 13secs.

==================================================
INPUT
==================================================

{base_message}

==================================================
FINAL RESPONSE
==================================================
"""

    return llm.generate(prompt).strip()