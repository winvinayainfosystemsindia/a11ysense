import pytest
import json
from app.core.pricing import estimate_cost
from app.core.compression import compress_prompt
from app.core.cache import _generate_cache_key, get_cached_completion, set_cached_completion
from app.core.router import CentralLLMRouter, track_session_tokens, get_session_summary
from app.schemas.llm import GenerateRequest

def test_pricing_estimation():
    """
    Validates cost calculations across different providers and models.
    """
    # Claude Haiku pricing: input $0.25/1M, output $1.25/1M
    cost_haiku = estimate_cost("claude-3-haiku-20240307", 1000000, 1000000)
    assert cost_haiku == 1.50  # 0.25 + 1.25

    # Gemini Flash pricing: input $0.075/1M, output $0.30/1M
    cost_flash = estimate_cost("gemini-1.5-flash", 1000000, 1000000)
    assert cost_flash == 0.375  # 0.075 + 0.30

    # Unknown model fallback (uses llama-3.1-8b-instant rates: input $0.05/1M, output $0.08/1M)
    cost_unknown = estimate_cost("some-future-model", 1000000, 1000000)
    assert cost_unknown == 0.13  # 0.05 + 0.08

def test_prompt_compression_whitespace():
    """
    Validates that redundant whitespaces and newlines are compressed.
    """
    prompt = "Hello      World!\n\n\nHow    are\n\nyou?"
    compressed = compress_prompt(prompt)
    assert "Hello World!" in compressed
    assert "How are" in compressed
    # Repeated newlines compressed to single newlines
    assert "\n\n\n" not in compressed

def test_prompt_compression_html_truncation():
    """
    Validates that extremely large nested HTML blocks are truncated for token efficiency.
    """
    # Create an HTML block greater than 1000 chars
    large_inner = "x" * 1200
    large_html = f"<div>{large_inner}</div>"
    prompt = f"Analyze this violation: {large_html}"
    
    compressed = compress_prompt(prompt)
    assert "[HTML truncated for token efficiency" in compressed
    assert "x" * 1200 not in compressed

def test_cache_mechanism():
    """
    Validates in-memory and serialization cache mechanism.
    """
    prompt = "Test Prompt"
    system = "Test System"
    res_data = {"text": "Test Response", "provider": "mock", "model": "mock-model"}
    
    # Set cached completion
    set_cached_completion(prompt, system, res_data)
    
    # Retrieve cached completion
    cached_val = get_cached_completion(prompt, system)
    assert cached_val is not None
    assert cached_val["text"] == "Test Response"
    assert cached_val["provider"] == "mock"

def test_session_token_tracking():
    """
    Validates session state accumulation and USD cost tracking.
    """
    session_id = "test-session-123"
    
    # Cumulative track requests
    track_session_tokens(session_id, "mock", 100, 200, 0.005)
    track_session_tokens(session_id, "mock", 150, 250, 0.008)
    
    summary = get_session_summary(session_id)
    assert summary.session_id == session_id
    assert summary.total_requests == 2
    assert summary.total_input_tokens == 250
    assert summary.total_output_tokens == 450
    assert summary.total_tokens == 700
    assert summary.total_cost_usd == 0.013
    assert summary.provider_breakdown["mock"] == 2

@pytest.mark.asyncio
async def test_mock_llm_router_resolution():
    """
    Validates execution fallback and mock routing.
    """
    router = CentralLLMRouter()
    request = GenerateRequest(
        prompt="Auditing issue context",
        system_message="System rule",
        provider="mock",
        session_id="mock-session"
    )
    
    res = await router.execute_generate(request)
    assert res.provider == "mock"
    assert res.model == "mock"
    assert res.input_tokens > 0
    assert res.output_tokens > 0
    
    # Parse returned text is a valid JSON
    parsed = json.loads(res.text)
    assert "friendly_name" in parsed
    assert "wcag_criteria" in parsed
    assert "severity" in parsed
