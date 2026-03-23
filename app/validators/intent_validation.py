def validate_intent(intent):

    if not any([
        intent.metric,
        intent.aggregation,
        intent.analysis,
        intent.service
    ]):
        return False

    return True