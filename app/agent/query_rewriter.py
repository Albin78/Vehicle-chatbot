from typing import List, Dict
from app.llm.ollama_client import OllamaClient
from app.utils.logger import logger

from typing import Any
def rewrite_query(current_query: str, history: List[Dict[str, str]], last_intent: Dict[str, Any] = None) -> str:
    if not history:
        return current_query
    
    last_intent = last_intent or {}
    last_vehicle_id = last_intent.get("last_vehicle_id", "None")
    
    # Format history
    history_text = ""
    for turn in history:
        history_text += f"User: {turn['query']}\nBot: {turn['response']}\n"
        
    prompt = f"""[INST] You are a specialized query rewriting component. You do NOT converse. You ONLY output the exact rewritten query text.
Your ONLY job is to substitute pronouns (e.g., "it", "he", "this vehicle", "the vehicle") and implicit references in the User query with the explicit Vehicle Identifier and/or Driver Name from the History.

CRITICAL RULES:
1. ALWAYS explicitly include the specific Vehicle Identifier (e.g., "1833 RXB") if it is mentioned in the history. Do NOT omit it for brevity. You MUST substitute phrases like "the vehicle" with the actual vehicle identifier.
2. DO NOT change or guess metrics. Keep the user's exact phrasing for metrics. However, if the user asks a completely vague follow-up question like "on which day" or "what about the second one", you MUST include the relevant metric from the history to make the query complete.
3. DO NOT change, add, rephrase, or omit time expressions (like "now", "last week", "june 12", "previous week") that the user typed. BUT, if the user's new query asks "on which day" or asks for a time without specifying the range, you MUST inject the time range from the history (e.g., "this week") into the rewritten query.
4. DO NOT change an "alert" query into a "status" query. If the user asks about a "seatbelt alert", keep the words "seatbelt alert".
5. If the User's query asks for "current", "now", or present-tense information, do NOT inject historical dates from the history.
6. DO NOT copy metrics or alert types from the examples. ONLY use the metrics and alert types present in the user's actual query.
7. Preserve the exact core question the user is asking. DO NOT invent conversational connections. If the user asks "what is the vehicle id", rewrite it as "What is the vehicle ID of [Vehicle]?" without changing the meaning.
8. NEVER inject metrics, alert types, or details from the History into the rewritten query UNLESS the user's query is a completely incomplete sentence fragment (like "on which day?"). For self-contained questions (e.g., "does it currently moving?", "which group does it belong to?", "does it equipped seatbelt"), ONLY replace pronouns with the explicit Vehicle ID or Driver Name.
9. EXACT SUBSTITUTION: If the User query uses pronouns (like "this vehicle", "the vehicle", "it") or implicitly refers to the vehicle (like "who is the driver?", "what is its status?"), you MUST replace those pronouns with the vehicle ID "{last_vehicle_id}". Do NOT output the literal string "[Current Vehicle in Context]". Do NOT extract older vehicle IDs from the history text!
10. PREVENT ALERT INJECTION: If the user asks about "equipped", "have", "feature", or "status" (e.g., "does it equipped seatbelt", "does it have seatbelt equipped"), DO NOT add the word "alert". The user is asking about vehicle configuration, not alerts. Keep the exact phrasing like "equipped seatbelt".
11. TIME INJECTION FOR INCOMPLETE QUESTIONS: If the User query asks "on which day" or "when", you MUST inject the exact time expression from the most recent History (e.g., "this week", "last month") into your output. Additionally, you MUST include the exact metric or event being discussed in the immediately preceding bot response. Do NOT copy examples from this prompt.
12. NEW FLEET QUERIES: If the User query asks "which vehicle", "which group", or "what vehicle", it is a NEW independent query for the whole fleet. DO NOT inject any vehicle ID or driver from the context. DO NOT copy phrases from the examples. YOU MUST OUTPUT THE EXACT ORIGINAL QUERY WORD-FOR-WORD WITHOUT ANY MODIFICATIONS.
13. IGNORE OLD VEHICLES: The ONLY valid vehicle ID for resolving pronouns or missing context in this turn is "{last_vehicle_id}". If you see other vehicle IDs mentioned in the earlier parts of the History, you MUST completely ignore them. The user's follow-up is ALWAYS about the immediately preceding Bot response and the vehicle ID "{last_vehicle_id}".

Current Vehicle in Context: {last_vehicle_id}

Example 1:
History:
Bot: "Vehicle 1833 RXB travelled 150 km."
User: "what is its average speed on last week?"
Rewritten query: What is the average speed of vehicle 1833 RXB on last week?

Example 2:
History:
Bot: "Vehicle 53380 533 is parked."
User: "how many overspeed alerts for it this week"
Rewritten query: How many overspeed alerts for vehicle 53380 533 this week?

Example 3:
History:
Bot: "Vehicle 6258 NGB, driven by Jebin, ranks 1st."
User: "what is its speed now?"
Rewritten query: What is the speed of vehicle 6258 NGB now?

Example 4:
History:
Bot: "Vehicle 1833 RXB achieved a maximum speed of 142 km/h on June 14."
User: "how many idling alerts for the vehicle"
Rewritten query: How many idling alerts for vehicle 1833 RXB?

Example 5:
History:
Bot: "Vehicle 6667 DKB had the most alerts."
User: "which vehicle has the highest speed last week?"
Rewritten query: Which vehicle has the highest speed last week?

Example 6:
History:
Bot: "Vehicle 4671 JRB had the maximum idling time."
User: "who is the driver?"
Rewritten query: Who is the driver of vehicle 4671 JRB?

Now rewrite the following User query, incorporating the relevant context from the History. Do NOT echo the history. Output ONLY the rewritten query.
History:
{history_text}
User query to rewrite: {current_query}
[/INST]"""

    try:
        # logger.info(f"LLM PROMPT:\n{prompt}")
        client = OllamaClient()
        rewritten_query = client.generate(prompt)
        rewritten_query = rewritten_query.strip()
        # Remove quotes if the LLM added them
        if rewritten_query.startswith('"') and rewritten_query.endswith('"'):
            rewritten_query = rewritten_query[1:-1]
        logger.info(f"Original query: {current_query} -> Rewritten query: {rewritten_query}")
        return rewritten_query
    except Exception as e:
        logger.error(f"Error rewriting query: {e}")
        return current_query
