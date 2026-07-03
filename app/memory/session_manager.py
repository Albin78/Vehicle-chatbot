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
        
        # Fix #8: keep only 1 turn — query_rewriter uses only history[-1],
        # so storing more than 1 turn wastes memory with no benefit.
        self.sessions[session_id]["history"].append({"query": query, "response": response})
        if len(self.sessions[session_id]["history"]) > 1:
            self.sessions[session_id]["history"].pop(0)

        # Store last intent specifics
        if intent:
            # We store it carefully handling cases where intent might be None or a dict (if error)
            # Prioritize the actual returned API result to preserve proper formatting (e.g. spaces)
            updated_from_result = False
            extracted_vid = None
            if isinstance(result, dict):
                if result.get("numberPlate"):
                    extracted_vid = result["numberPlate"]
                    updated_from_result = True
                elif result.get("vehicle") and isinstance(result["vehicle"], str):
                    extracted_vid = result["vehicle"]
                    updated_from_result = True
                elif "vehicle" in result and isinstance(result["vehicle"], dict) and result["vehicle"].get("numberPlate"):
                    extracted_vid = result["vehicle"]["numberPlate"]
                    updated_from_result = True
                elif result.get("query_type") == "ranked_alerts" and result.get("ranked"):
                    # Fallback to the first vehicle in the ranked list
                    first_item = result["ranked"][0]
                    if first_item.get("numberPlate"):
                        extracted_vid = first_item["numberPlate"]
                        updated_from_result = True
            elif isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict) and result[0].get("numberPlate"):
                extracted_vid = result[0]["numberPlate"]
                updated_from_result = True
                
            if updated_from_result and extracted_vid:
                self.sessions[session_id]["last_intent"]["last_vehicle_id"] = extracted_vid
            elif hasattr(intent, "vehicle_id") and intent.vehicle_id:
                self.sessions[session_id]["last_intent"]["last_vehicle_id"] = intent.vehicle_id
            elif hasattr(intent, "source") and intent.source == "fleet_analytics" and not intent.vehicle_id:
                # Clear the last vehicle ID if it's a general fleet query with no vehicle
                self.sessions[session_id]["last_intent"]["last_vehicle_id"] = None
            
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
