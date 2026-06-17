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
3. DO NOT change, add, rephrase, or omit time expressions (like "now", "last week", "june 12", "previous week"). Keep them EXACTLY as the user typed them.
4. DO NOT change an "alert" query into a "status" query. If the user asks about a "seatbelt alert", keep the words "seatbelt alert".
5. If the User's query asks for "current", "now", or present-tense information, do NOT inject historical dates from the history.
6. DO NOT copy metrics or alert types from the examples. ONLY use the metrics and alert types present in the user's actual query.
7. Preserve the exact core question the user is asking. DO NOT invent conversational connections. If the user asks "what is the vehicle id", rewrite it as "What is the vehicle ID of [Vehicle]?" without changing the meaning.
8. NEVER inject metrics, alert types, or details from the History into the rewritten query UNLESS the user's query is a completely incomplete sentence fragment (like "on which day?"). For self-contained questions (e.g., "does it currently moving?", "which group does it belong to?"), ONLY replace pronouns with the explicit Vehicle ID or Driver Name.
9. EXACT SUBSTITUTION: If the User query uses "this vehicle", "the vehicle", or "it", and the Current Vehicle in Context is not 'None', you MUST substitute those exact pronouns with the Current Vehicle ID. DO NOT use descriptive phrases like "the vehicle with the most alerts". Just use the ID!

Current Vehicle in Context: {last_vehicle_id}

Example 1:
History:
Bot: "Vehicle 1833 RXB travelled 150 km."
User: "what is its average speed on last week?"
Rewritten query: What is the average speed of vehicle 1833 RXB on last week?

Example 2:
History:
Bot: "Driver Vipin Kunookkara is assigned to vehicle 53380 533."
User: "Does it have harsh braking alert on june 10"
Rewritten query: Does vehicle 53380 533 have harsh braking alert on june 10?

Example 3:
History:
Bot: "Vehicle 6258 NGB, driven by Jebin, ranks 1st."
User: "what is its speed now?"
Rewritten query: What is the speed of vehicle 6258 NGB now?

Example 4:
History:
Bot: "Vehicle 1833 RXB achieved a maximum speed of 142 km/h on June 14."
User: "who drove the vehicle?"
Rewritten query: Who drove vehicle 1833 RXB?

Now rewrite the following User query, incorporating the relevant context from the History. Do NOT echo the history. Output ONLY the rewritten query.
History:
{history_text}
User query to rewrite: {current_query}
[/INST]"""

    try:
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
