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
        
    prompt = f"""You are a helpful query rewriter for a vehicle management system.
Rewrite the user's current input into a fully standalone query using context from the conversation history. Do not answer the query, only rewrite it. If it is already standalone, return it as is.
CRITICAL INSTRUCTION: If the Bot's response in the history mentions a specific vehicle identifier (e.g., 53380 533, 1833 RXB, 6667 DKB) and the user's follow-up query is related to it, you MUST explicitly include this exact vehicle identifier in your rewritten query.

Example:
Bot: "Driver Vipin Kunookkara is assigned to vehicle 53380 533 and achieved a max speed of 121.0 km/h."
User: "On which date did this happen?"
Rewritten Output: "On which date did vehicle 53380 533 achieve the maximum speed of 121.0 km/h?"

Conversation History:
{history_text}
Current User Input: {current_query}

Rewritten Output:"""

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
