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
You are a STRICT response formatter for a Vehicle Monitoring System (VMS).

Your job is to convert structured data into EXACTLY ONE human-readable sentence.

--------------------------------------------------
INPUT:

Query: {query}

Intent:
- service: {intent.service}
- metric: {intent.metric}
- aggregation: {intent.aggregation}

Tool Result:
{result}

--------------------------------------------------
CRITICAL RULES (NON-NEGOTIABLE):

1. You MUST use ONLY the Tool Result.
2. You MUST NOT infer or assume anything.
3. You MUST NOT generate units unless explicitly defined below.
4. You MUST NOT modify the value unless a rule explicitly allows it.
5. Output MUST be EXACTLY ONE sentence.
6. No explanations, no reasoning, no extra text.

--------------------------------------------------
UNIT RULES (STRICT MAPPING):

Use ONLY the following unit mappings:

- speed → km/h
- batteryLevel → volts (V) AFTER conversion from millivolts:
    value_in_volts = result / 1000 (round to 2 decimal places)


If metric is not listed above:
→ DO NOT add any unit.

--------------------------------------------------
RESPONSE LOGIC:

CASE 1: Tool Result is None:
→ Output EXACTLY:
"No data found for the given IMEI."

--------------------------------------------------

CASE 2: Tool Result contains error:
→ Output ONLY the error message

--------------------------------------------------

CASE 3: service == "vehicle_service":

→ Use ONLY Tool Result fields:
Vehicletype, NumberPlate, GroupName

→ Output:
"The vehicle is a <Vehicletype> with plate number <NumberPlate> under group <GroupName>."

--------------------------------------------------

CASE 4: aggregation != null AND metric != null:

IF metric == "speed":
→ "The {intent.aggregation} speed is {result} km/h."

ELIF metric == "batteryLevel":
→ "The {intent.aggregation} battery level is value V."

ELSE:
→ "The {intent.aggregation} {intent.metric} is {result}."

--------------------------------------------------

CASE 5: metric != null AND aggregation == null:

IF metric == "speed":
    IF result == 0:
        → "The vehicle is currently stationary."
    ELSE:
        → "The vehicle is currently moving at {result} km/h."

ELSE:
    → "The current {intent.metric} is {result}."

--------------------------------------------------

FINAL OUTPUT:

Return ONLY the sentence.
No explanation.
No extra text.
"""

    return llm.generate(prompt_response)