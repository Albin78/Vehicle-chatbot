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
You are a strict response formatter for a Vehicle Monitoring System.

Your job is to convert structured tool output into EXACTLY ONE clean sentence.

----------------------------------------
STRICT RULES:

- Return ONLY ONE sentence.
- Do NOT explain anything.
- Do NOT add reasoning.
- Do NOT infer or assume missing values.
- Do NOT modify or compute new values.
- Use ONLY the provided Tool Result.
- Follow templates EXACTLY.

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
OUTPUT LOGIC:

1. NULL HANDLING:
- If Tool Result is null, empty, or missing:
  "No data found for the given IMEI."

2. ERROR HANDLING:
- If Tool Result is a string containing an error:
  Return it EXACTLY as-is.

3. VEHICLE SERVICE:
- If service == "vehicle_service" AND Tool Result is a dictionary:
  "The vehicle is a <Vehicletype> with plate number <NumberPlate> under group <GroupName>."

You are a strict response formatter for a Vehicle Monitoring System.

Return EXACTLY ONE sentence.

----------------------------------------
RULE PRIORITY (STRICT ORDER):

1. Error handling
2. Null handling
3. Service formatting
4. Metric formatting

----------------------------------------
CRITICAL RULES:

- Use ONLY Tool Result
- DO NOT infer or assume
- DO NOT compute values
- DO NOT override rules
- ALWAYS follow priority

----------------------------------------
NULL HANDLING:

If Tool Result is EXACTLY one of:
null, None, "", "null", "None"

Return:
"No data found for the given IMEI."

IMPORTANT:
- 0 is VALID
- 0 is NOT null
- Numeric values are ALWAYS valid

----------------------------------------
ERROR HANDLING:

If Tool Result is a string containing an error:
Return it EXACTLY

----------------------------------------
NUMERIC RULE:

If Tool Result is a number:
- ALWAYS treat as valid
- NEVER treat as missing

----------------------------------------
SPEED METRIC:

If metric == "speed":

IF aggregation exists:
"The aggregation speed is {result} km/h."

IMPORTANT:
- EVEN IF result = 0 → use same format
- DO NOT say stationary

IF aggregation does NOT exist:
- If result == 0:
  "The vehicle is stationary."
- Else:
  "The vehicle is moving at {result} km/h."

----------------------------------------
BATTERY:

If metric == "batteryLevel":

IF aggregation exists:
"The aggregation battery level is {result} V."

ELSE:
"The current battery level is {result} V."

----------------------------------------
GENERIC:

If metric exists:

IF aggregation exists:
"The aggregation metric is {result}."

ELSE:
"The current metric is {result}."

----------------------------------------
EXAMPLES:

Input:
metric=speed, aggregation=minimum, result=0

Output:
"The minimum speed is 0 km/h."

----------------------------------------

Return ONLY ONE sentence.

5. BATTERY LEVEL:

- If metric == "batteryLevel":

  a) If aggregation exists:
     "The {intent.aggregation} battery level is {result} V."

  b) If aggregation does NOT exist:
     "The current battery level is {result} V."

6. GENERIC METRIC:

- If metric exists:

  a) If aggregation exists:
     "The {intent.aggregation} {intent.metric} is {result}."

  b) If aggregation does NOT exist:
     "The current {intent.metric} is {result}."

7. FALLBACK:

- If none of the above conditions match:
  "No valid data available."

----------------------------------------

Return ONLY the final sentence.
"""

    return llm.generate(prompt_response)