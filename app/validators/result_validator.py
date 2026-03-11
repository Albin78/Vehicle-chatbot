def validate_result(result):

    if result is None:
        raise ValueError("Tool returned empty result")

    return True