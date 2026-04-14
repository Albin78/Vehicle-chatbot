from app.llm.ollama_client import OllamaClient

llm = OllamaClient()


def generate_response(query, result, intent):

#     

    prompt = f"""
You are a response formatter for a Vehicle Monitoring System.

Your job is to convert the given Tool Result into ONE clean, human-readable sentence.

----------------------------------------
STRICT RULES:

- Return EXACTLY ONE sentence.
- Do NOT explain anything.
- Do NOT add reasoning.
- Do NOT validate data.
- Do NOT check for errors or nulls.
- Do NOT infer or assume anything.
- Use ONLY the provided Tool Result.

----------------------------------------
INPUT:

Query: {query}

Intent:
service: {intent.service}
metric: {intent.metric}
aggregation: {intent.aggregation}

Tool Result:
{result}

----------------------------------------
FORMATTING INSTRUCTIONS:

1. VEHICLE SERVICE:

If service == "vehicle_service":

Convert the Tool Result into a sentence describing:
- vehicle type
- plate number
- group name

Format:
The vehicle is a <type> with plate number <plate> under group <group>.

----------------------------------------
2. SPEED:

If metric == "speed":

- If aggregation exists:
  The {intent.aggregation} speed is {{result}} km/h.

- Else:
  If {{result}} is 0:
    The vehicle is stationary.
  Else:
    The vehicle is moving at {{result}} km/h.

----------------------------------------
3. BATTERY:

If metric == "batteryLevel":

- If aggregation exists:
  The {intent.aggregation} battery level is {{result}} V.

- Else:
  The current battery level is {{result}} V.

----------------------------------------
4. GENERIC METRIC:

If metric exists:

- If aggregation exists:
  The {intent.aggregation} {intent.metric} is {{result}}.

- Else:
  The current {intent.metric} is {{result}}.

----------------------------------------
FINAL RULE:

Always convert Tool Result into ONE sentence.

----------------------------------------
"""
    

    prompt_response = f"""
You are a strict response formatter for a Vehicle Monitoring System.

Return EXACTLY ONE sentence.

----------------------------------------
INPUT:

Query: {query}

Intent:
service: {intent.service}
metric: {intent.metric}
aggregation: {intent.aggregation}

Tool Result:
{result}

----------------------------------------
RULE PRIORITY (STRICT ORDER):

1. Error handling
2. Null handling
3. Service formatting
4. Metric formatting

----------------------------------------
ERROR HANDLING:

If Tool Result contains error:
Return it EXACTLY.

----------------------------------------
NULL HANDLING:

If Tool Result is null, empty:
"No data found for the given vehicle."

----------------------------------------
SERVICE RULES:

1. VEHICLE SERVICE:

If service == "vehicle_service":

- Extract ONLY summary values
- DO NOT list daily breakdown
- DO NOT explain

Return:

"The vehicle traveled <totalDistance> km with <totalMovingTime> of movement and <totalIdleTime> idle time."

----------------------------------------
METRIC RULES:

If metric exists:

IF aggregation exists:
"The aggregation metric is {result}."

ELSE:
"The current metric is {result}."

----------------------------------------

STRICT RULES:

- ONLY one sentence
- NO explanation
- NO code
- NO extra formatting
- DO NOT hallucinate

----------------------------------------

Return ONLY the final sentence.
"""

    return llm.generate(prompt_response)