from typing import List, Dict
from app.llm.ollama_client import OllamaClient
from app.utils.logger import logger

def rewrite_query(current_query: str, history: List[Dict[str, str]]) -> str:
    if not history:
        return current_query
    
    # Format history
    history_text = ""
    for turn in history:
        history_text += f"User: {turn['query']}\nBot: {turn['response']}\n"
        
    prompt = f"""[INST] You are a specialized query rewriting component. You do NOT converse. You ONLY output the exact rewritten query text.
If the history mentions a specific vehicle identifier (e.g., 53380 533, 1833 RXB, 6667 DKB, etc.), explicitly include this exact vehicle identifier in your rewritten query.
CRITICAL REFERENCE RULE: If the User's query contains pronouns ("it", "he", "they") or ordinal references ("the first one", "the second driver", "the last vehicle"), you MUST substitute these references with BOTH the exact Driver Name AND their exact Vehicle Identifier from the history (e.g., "Vehicle 6258 NGB driven by Jebin"). NEVER refer to a driver without also including their Vehicle Identifier.
CRITICAL DATE RULE: If the User's query asks for "current", "latest", "now", or present-tense information (e.g., "what is its current speed?"), you MUST NOT include any historical dates (like "June 15") from the history in your rewritten query.

Example 1:
History:
Bot: "Driver Vipin Kunookkara is assigned to vehicle 53380 533 and achieved a max speed of 121.0 km/h."
User: "On which date did this happen?"
Rewritten query: On which date did vehicle 53380 533 achieve the maximum speed of 121.0 km/h?

Example 2:
History:
Bot: "Vehicle 1833 RXB travelled 150 km."
User: "What was its max speed?"
Rewritten query: What was the maximum speed of vehicle 1833 RXB?

Example 3:
History:
Bot: "Vehicle 6258 NGB, driven by Jebin, ranks 1st. Vehicle 6667 DKB, driven by Rubel, ranks 2nd."
User: "which vehicle did the first driver drive?"
Rewritten query: Which vehicle did the first driver (Jebin driving Vehicle 6258 NGB) drive?

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
