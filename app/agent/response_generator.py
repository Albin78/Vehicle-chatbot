from app.llm.ollama_client import OllamaClient

llm = OllamaClient()


def generate_response(query, result, intent):

#     

    prompt = f"""
You are a VMS (Vehicle Monitoring System) assistant.

User Query: {query}
Tool Result: {result}
Intent:
- metric: {intent.metric}
- aggregation: {intent.aggregation}
- service: {intent.service}

--------------------------------------------------
CRITICAL RULES (STRICT EXECUTION):

1. TOOL RESULT PRIORITY:
- If Tool Result is NOT empty:
  → You MUST answer using it
  → DO NOT ignore it
  → DO NOT generate generic responses

2. RESTRICTED ACTIONS:
If query asks to delete, update, modify:
→ "This action is not permitted."

3. OUT-OF-CONTEXT:
If ALL intent fields are null:
→ "I am a VMS chatbot, I am unable to answer this question."

4. VEHICLE DETAILS HANDLING:

IF service == "vehicle_service":

    CASE A: Specific field requested:
    → Return ONLY that field

    CASE B: General query (e.g., "fetch details"):
    → Return a concise summary:

    → DO NOT ask questions
    → DO NOT fallback

5. TELEMETRY HANDLING:

IF metric is NOT null:

    A. CURRENT VALUE (aggregation is null):

        IF metric == "speed":
            IF value == 0:
                → "The vehicle is currently stationary."
            ELSE:
                → "The vehicle is currently moving at <value> km/h."

        ELSE:
            → "The current <metric> is <value> <unit>."

    B. AGGREGATION:

        → "The <aggregation> <metric> is <value> <unit>."

        → DO NOT apply stationary rule

--------------------------------------------------
STYLE RULES:

- ONE short sentence
- No explanation
- No extra text
- No assumptions

--------------------------------------------------
METRIC UNITS:

- batteryLevel → mV
- speed → km/h
- engineRpm → RPM
- engineTemperature → °C
"""
    

    prompt_response = f"""
You are a response formatter for a Vehicle Monitoring System.

Return ONLY ONE sentence.
Do NOT explain.
Do NOT describe steps.
Do NOT include reasoning.
Do NOT add extra text.

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

RULES:

- Use ONLY the Tool Result.
- Do NOT create or assume new values.
- Do NOT compute new variables.

----------------------------------------

OUTPUT:

1. If Tool Result is null:
"No data found for the given IMEI."

2. If Tool Result is an error string:
Return it exactly.

3. If service is "vehicle_service":
"The vehicle is a <Vehicletype> with plate number <NumberPlate> under group <GroupName>."

4. If metric is "speed":
    If aggregation exists:
        "The {intent.aggregation} speed is {result} km/h."
    Else:
        If result == 0:
            "The vehicle is stationary."
        Else:
            "The vehicle is moving at {result} km/h."

5. If metric is "batteryLevel":
    If aggregation exists:
        "The {intent.aggregation} battery level is {result} V."
    Else:
        "The current battery level is {result} V."

6. If metric exists:
    If aggregation exists:
        "The {intent.aggregation} {intent.metric} is {result}."
    Else:
        "The current {intent.metric} is {result}."

----------------------------------------

Return ONLY the final sentence.
"""

    return llm.generate(prompt_response)