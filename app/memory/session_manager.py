from typing import Dict, List, Any, Optional
from app.schemas.intent_schema import QueryIntent
from app.utils.logger import logger

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        if not session_id or session_id not in self.sessions:
            return []
        return self.sessions[session_id].get("history", [])

    def add_interaction(self, session_id: str, query: str, response: str, intent: Optional[QueryIntent], result: Any = None):
        if not session_id:
            return
            
        if session_id not in self.sessions:
            self.sessions[session_id] = {"history": [], "last_intent": {}}
        
        # Keep last 3 turns
        self.sessions[session_id]["history"].append({"query": query, "response": response})
        if len(self.sessions[session_id]["history"]) > 3:
            self.sessions[session_id]["history"].pop(0)

        # Store last intent specifics
        if intent:
            # We store it carefully handling cases where intent might be None or a dict (if error)
            # Assuming intent is a QueryIntent model at this point, but checking with getattr just in case
            if hasattr(intent, "vehicle_id") and intent.vehicle_id:
                self.sessions[session_id]["last_intent"]["last_vehicle_id"] = intent.vehicle_id
            elif isinstance(result, dict):
                if result.get("numberPlate"):
                    self.sessions[session_id]["last_intent"]["last_vehicle_id"] = result["numberPlate"]
                elif "vehicle" in result and isinstance(result["vehicle"], dict) and result["vehicle"].get("numberPlate"):
                    self.sessions[session_id]["last_intent"]["last_vehicle_id"] = result["vehicle"]["numberPlate"]
                elif result.get("query_type") == "ranked_alerts" and result.get("ranked"):
                    # Fallback to the first vehicle in the ranked list
                    first_item = result["ranked"][0]
                    if first_item.get("numberPlate"):
                        self.sessions[session_id]["last_intent"]["last_vehicle_id"] = first_item["numberPlate"]
            elif isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict) and result[0].get("numberPlate"):
                self.sessions[session_id]["last_intent"]["last_vehicle_id"] = result[0]["numberPlate"]
            
            if hasattr(intent, "metrics"):
                self.sessions[session_id]["last_intent"]["last_metric"] = intent.metrics
            if hasattr(intent, "source"):
                self.sessions[session_id]["last_intent"]["last_source"] = intent.source
                
        logger.info(f"[SESSION MEMORY] Session {session_id} updated: history length {len(self.sessions[session_id]['history'])}, last_intent={self.sessions[session_id].get('last_intent')}")
            
    def get_last_intent(self, session_id: str) -> Dict[str, Any]:
        if not session_id or session_id not in self.sessions:
            return {}
        return self.sessions[session_id].get("last_intent", {})

session_manager = SessionManager()
