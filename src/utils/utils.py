GPT_MINI_INPUT = 0.150 / 1_000_000
GPT_MINI_OUTPUT = 0.600 / 1_000_000

GROQ_LLAMA_INPUT = 0.05 / 1_000_000
GROQ_LLAMA_OUTPUT = 0.08 / 1_000_000


def calculate_cost(tokens, model):

    if model == 'gpt-4o-mini':
        cost = (tokens["prompt_tokens"] * GPT_MINI_INPUT) + (
            tokens["completion_tokens"] * GPT_MINI_OUTPUT
        )
    elif model == 'llama-3.1-8b-instant':
        cost = (tokens["prompt_tokens"] * GROQ_LLAMA_INPUT) + (
            tokens["completion_tokens"] * GROQ_LLAMA_OUTPUT
        )

    return cost
