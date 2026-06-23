from typing import List, Dict
from app.llm.ollama_client import OllamaClient
from app.utils.logger import logger

from typing import Any
def rewrite_query(current_query: str, history: List[Dict[str, str]], last_intent: Dict[str, Any] = None) -> str:
    if not history:
        return current_query
    
    last_intent = last_intent or {}
    last_vehicle_id = last_intent.get("last_vehicle_id") or None
    
    # If there is no vehicle in context (e.g., after a fleet query) and the user
    # is using pronouns that refer to a vehicle, we cannot resolve them.
    # Return the original query so the downstream pipeline can ask for a vehicle ID
    # instead of the LLM hallucinating a random vehicle from the response list.
    if not last_vehicle_id:
        import re
        vehicle_pronouns = re.compile(
            r'\b(its|it|this vehicle|the vehicle|that vehicle|this|these|those)\b', re.IGNORECASE
        )
        if vehicle_pronouns.search(current_query):
            logger.info(
                f"[QUERY REWRITER] No vehicle in context and query uses pronouns — "
                f"skipping rewrite: {current_query}"
            )
            return current_query
        # For non-pronoun follow-ups (fleet-to-fleet), set a safe placeholder
        last_vehicle_id = "None"
    
    # Format history - Only use the LAST turn to prevent LLM confusion and hallucinations
    history_text = ""
    if history:
        last_turn = history[-1]
        history_text = f"User: {last_turn['query']}\nBot: {last_turn['response']}\n"
        
    prompt = f"""[INST] You are a specialized query rewriting component. You do NOT converse. You ONLY output the exact rewritten query text.
Your ONLY job is to substitute pronouns (e.g., "it", "he", "this vehicle", "the vehicle") and implicit references in the User query with the explicit Vehicle Identifier and/or Driver Name from the History.

CRITICAL RULES:
1. ALWAYS explicitly include the specific Vehicle Identifier (e.g., "1833 RXB") if it is mentioned in the history. Do NOT omit it for brevity. You MUST substitute phrases like "the vehicle" with the actual vehicle identifier.
2. DO NOT change or guess metrics. Keep the user's exact phrasing for metrics. If the user asks a new metric (like "current location", "speed", "status"), DO NOT copy the metric from the previous query.
3. EXPLICIT VEHICLE CHECK: If the user's query ALREADY contains a specific vehicle identifier (like "1832RXB" or "6667 DKB") AND does not use any pronouns ("it", "this vehicle"), DO NOT REWRITE IT! Output the EXACT original query word-for-word.
4. DO NOT change, add, rephrase, or omit time expressions (like "now", "last week", "june 12", "previous week") that the user typed. BUT, if the user's new query asks "on which day" or asks for a time without specifying the range, you MUST inject the time range from the history (e.g., "this week") into the rewritten query.
5. DO NOT change an "alert" query into a "status" query. If the user asks about a "seatbelt alert", keep the words "seatbelt alert".
6. If the User's query asks for "current", "now", or present-tense information, do NOT inject historical dates from the history.
7. DO NOT copy metrics or alert types from the examples or the history. ONLY use the metrics and alert types present in the user's actual query.
8. NEVER inject the previous question from the History into the rewritten query. If the user asks for "current location", do NOT output "who is the driver". ONLY replace pronouns with the explicit Vehicle ID.
9. EXACT SUBSTITUTION: If the User query uses pronouns (like "this vehicle", "the vehicle", "it") or implicitly refers to the vehicle (like "who is the driver?", "what is its status?"), you MUST replace those pronouns with the vehicle ID "{last_vehicle_id}". Do NOT output the literal string "[Current Vehicle in Context]". Do NOT extract older vehicle IDs from the history text!
10. PREVENT ALERT INJECTION: If the user asks about "equipped", "have", "feature", or "status" (e.g., "does it equipped seatbelt", "does it have seatbelt equipped"), DO NOT add the word "alert". The user is asking about vehicle configuration, not alerts. Keep the exact phrasing like "equipped seatbelt".
11. TIME INJECTION FOR INCOMPLETE QUESTIONS: If the User query asks "on which day" or "when", you MUST inject the exact time expression from the most recent History (e.g., "this week", "last month") into your output. Additionally, you MUST explicitly state the actual subject of the previous sentence (e.g. "have its highest speed", "have its lowest speed") instead of using vague words like "happen" or "event". NEVER write "What happened".
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

Example 7:
History:
Bot: "The driver of vehicle 6667 DKB is Rubel Miah Fajul."
User: "current location of this vehicle"
Rewritten query: current location of vehicle 6667 DKB

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
        
        with open("/tmp/query_rewrite_debug.log", "a") as f:
            f.write(f"last_vehicle_id: {last_vehicle_id}\n")
            f.write(f"history: {history_text}\n")
            f.write(f"original: {current_query}\n")
            f.write(f"rewritten: {rewritten_query}\n")
            f.write("-" * 50 + "\n")
            
        return rewritten_query
        logger.info(f"Original query: {current_query} -> Rewritten query: {rewritten_query}")
        return rewritten_query
    except Exception as e:
        logger.error(f"Error rewriting query: {e}")
        return current_query
