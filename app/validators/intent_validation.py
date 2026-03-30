def validate_intent(intent):
    

    if intent.service not in [None, "vehicle_service"]:
        return False
        
    if not any([
        intent.metric,
        intent.aggregation,
        intent.analysis,
        intent.service,
        intent.action
    ]):
        return False

    return True

