import json
from app.api.route import query_system
from app.schemas.request_schema import QueryRequest

queries = [
    # 1. Single Vehicle Queries (Structured)
    "what is the current status of vehicle 1832RXB?",
    "what is the maximum speed of vehicle 1832RXB over the last week?",
    "give me the alert history for 1832RXB yesterday",
    
    # 2. Single Vehicle Queries (Unstructured / Conversational)
    "hey, can you check on the current status for 1832RXB right now?",
    "i need to know the max speed that 1832RXB hit over the last week.",
    "is 1832RXB moving or stopped?",
    "what's going on with 1832RXB today?",
    
    # 3. Fleet-wide Queries (Structured)
    "what is the status of the entire fleet?",
    "which driver had the highest speed last week?",
    "how many overspeed alerts were there across the fleet?",
    "which vehicle travelled the most distance?",
    
    # 4. Fleet-wide Queries (Unstructured / Conversational)
    "give me a quick overview of how the entire fleet is doing right now",
    "how many vehicles are currently moving vs idling?",
    "i want to know who drove the fastest out of all the drivers last week",
    "which truck has covered the maximum mileage across the company?",
    "can you tell me which vehicle was idling the most recently?",
    "are there a lot of overspeed alerts? tell me how many we had across the whole fleet.",
    "which driver has the worst record for overspeeding?",
    "show me the distribution of different types of violations in the fleet.",
    "is anyone speeding right now?",
    "what's the total distance we drove as a company in the last 7 days?",
    "who is slacking off and idling the most?"
]

log_data = []

for q in queries:
    print(f"\n=======================")
    print(f"QUERY: {q}")
    req = QueryRequest(query=q)
    try:
        res = query_system(req)
        print(f"RESPONSE: {res.get('response')}")
        log_data.append({
            "query": q,
            "response": res.get('response')
        })
    except Exception as e:
        print(f"ERROR: {e}")
        log_data.append({
            "query": q,
            "error": str(e)
        })

with open("production_test_log.json", "w") as f:
    json.dump(log_data, f, indent=4)

print("\nSaved log to production_test_log.json")
