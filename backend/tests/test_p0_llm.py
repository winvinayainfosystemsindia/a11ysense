import os
import pytest
from unittest.mock import patch

from backend.app.core.llm.client import LLMClient, LLMUnavailableError


def test_llm_health():
    client = LLMClient()
    health = client.health()
    assert isinstance(health, dict)
    assert "claude" in health
    assert "gemini" in health
    assert "groq" in health
    for prov, status in health.items():
        assert status in ("OK", "NO_KEY", "SDK_MISSING")


@pytest.mark.asyncio
async def test_llm_unavailable_error_when_no_keys():
    # Force all keys to None
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "GEMINI_API_KEY": "", "GROQ_API_KEY": ""}):
        client = LLMClient()
        client.anthropic_key = None
        client.gemini_key = None
        client.groq_key = None

        with pytest.raises(LLMUnavailableError) as exc_info:
            await client.generate(prompt="Test prompt", use_cache=False)

        assert "All LLM providers failed" in str(exc_info.value)


def test_no_mock_fallback_method():
    client = LLMClient()
    assert not hasattr(client, "_mock_fallback"), "_mock_fallback must be deleted"
