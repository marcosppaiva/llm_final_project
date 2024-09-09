def calculate_cost(tokens, model):
    # TODO add cost for each model
    cost = (
        tokens['prompt_tokens'] * 0.0015 + tokens['completion_tokens'] * 0.002
    ) / 1000

    return cost
