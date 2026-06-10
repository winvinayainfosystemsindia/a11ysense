from typing import Dict

# Pricing in USD per 1 Million (1M) tokens
PRICING_MATRIX: Dict[str, Dict[str, float]] = {
    # Claude Models (Anthropic)
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
    
    # Gemini Models (Google GenAI)
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    
    # Llama Models (Groq)
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "llama3-70b-8192": {"input": 0.59, "output": 0.79},
    "llama3-8b-8192": {"input": 0.05, "output": 0.08},
    
    # Mock / Fallbacks
    "mock": {"input": 0.0, "output": 0.0}
}

def estimate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Estimates the USD cost of a completion request based on input and output token counts.
    If the model name is unknown, falls back to standard llama-3.1-8b-instant rates.
    """
    model_pricing = PRICING_MATRIX.get(model_name)
    if not model_pricing:
        # Fallback pricing to prevent failure on minor model variations
        for key in PRICING_MATRIX:
            if key in model_name:
                model_pricing = PRICING_MATRIX[key]
                break
        if not model_pricing:
            model_pricing = PRICING_MATRIX["llama-3.1-8b-instant"]

    input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
    output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
    return round(input_cost + output_cost, 6)
