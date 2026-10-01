"""
Unified Resilient LLM Client for A11ySense Monolith Backend.
Fallback hierarchy: Claude (Primary) -> Gemini (Fallback) -> Groq (Fallback) -> Mock (Emergency).
Integrated with DiskCache for performance & token efficiency.
"""
import os
import logging
from typing import Dict, Any, Optional
from backend.app.core.llm.cache import LLMCache

logger = logging.getLogger(__name__)

# Safely import LLM SDKs
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from groq import Groq
except ImportError:
    Groq = None


class LLMClient:
    def __init__(self):
        self.default_provider = os.getenv("LLM_PROVIDER", "claude").lower()
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.cache = LLMCache()

    async def generate(
        self,
        prompt: str,
        system_message: str = "",
        use_vision: bool = False,
        image_data: Optional[str] = None,
        provider: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generates text completion using the specified or fallback provider chain.
        Returns dict with: { "text": str, "input_tokens": int, "output_tokens": int, "model": str, "provider": str, "cached": bool }
        """
        target_provider = (provider or self.default_provider).lower()

        # Check Cache
        if use_cache:
            cached_res = self.cache.get(prompt, system_message, target_provider, use_vision)
            if cached_res:
                cached_res["cached"] = True
                return cached_res

        providers_to_try = [target_provider]
        for p in ["claude", "gemini", "groq"]:
            if p not in providers_to_try:
                providers_to_try.append(p)

        last_error = None
        for prov in providers_to_try:
            try:
                if prov == "claude" and self.anthropic_key and anthropic:
                    result = await self._generate_claude(prompt, system_message, use_vision, image_data)
                elif prov == "gemini" and self.gemini_key and genai:
                    result = await self._generate_gemini(prompt, system_message, use_vision, image_data)
                elif prov == "groq" and self.groq_key and Groq:
                    result = await self._generate_groq(prompt, system_message)
                else:
                    continue

                result["cached"] = False
                if use_cache and result.get("text"):
                    self.cache.set(prompt, result, system_message, target_provider, use_vision)
                return result

            except Exception as e:
                logger.warning(f"LLM Provider '{prov}' failed: {e}")
                last_error = str(e)
                continue

        # Emergency Mock Fallback
        logger.error(f"All LLM providers failed. Last error: {last_error}")
        return {
            "text": self._mock_fallback(prompt),
            "input_tokens": 50,
            "output_tokens": 100,
            "model": "mock-fallback",
            "provider": "mock",
            "cached": False,
            "error": last_error
        }

    async def _generate_claude(
        self, prompt: str, system_message: str, use_vision: bool, image_data: Optional[str]
    ) -> Dict[str, Any]:
        client = anthropic.Anthropic(api_key=self.anthropic_key)
        content = []
        if use_vision and image_data:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data,
                },
            })
        content.append({"type": "text", "text": prompt})

        kwargs = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": content}]
        }
        if system_message and system_message.strip():
            kwargs["system"] = system_message

        message = client.messages.create(**kwargs)
        text = message.content[0].text if message.content else ""
        return {
            "text": text,
            "input_tokens": getattr(message.usage, "input_tokens", 0),
            "output_tokens": getattr(message.usage, "output_tokens", 0),
            "model": "claude-sonnet-4-6",
            "provider": "claude"
        }

    async def _generate_gemini(
        self, prompt: str, system_message: str, use_vision: bool, image_data: Optional[str]
    ) -> Dict[str, Any]:
        genai.configure(api_key=self.gemini_key)
        model_name = "gemini-3.5-flash-lite"
        model = genai.GenerativeModel(model_name)

        parts = []
        if system_message:
            parts.append(system_message)
        parts.append(prompt)
        if use_vision and image_data:
            parts.append({"mime_type": "image/png", "data": image_data})

        response = model.generate_content(parts)
        text = response.text or ""
        in_tokens = getattr(response.usage_metadata, "prompt_token_count", len(prompt) // 4)
        out_tokens = getattr(response.usage_metadata, "candidates_token_count", len(text) // 4)

        return {
            "text": text,
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "model": model_name,
            "provider": "gemini"
        }

    async def _generate_groq(self, prompt: str, system_message: str) -> Dict[str, Any]:
        import httpx
        client = Groq(api_key=self.groq_key, http_client=httpx.Client())
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=4096
        )
        text = completion.choices[0].message.content or ""
        in_tokens = getattr(completion.usage, "prompt_tokens", 0)
        out_tokens = getattr(completion.usage, "completion_tokens", 0)

        return {
            "text": text,
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "model": "llama-3.1-8b-instant",
            "provider": "groq"
        }

    def _mock_fallback(self, prompt: str) -> str:
        return '{"friendly_name": "Accessibility Compliance Check", "wcag_criteria": "1.1.1", "wcag_level": "A", "severity": "Medium", "business_impact": "Users with screen readers may struggle to understand missing labels.", "expected_result": "All interactive elements have accessible names.", "actual_result": "Element lacks accessible label.", "remediation_plan": "Add aria-label or visible text node."}'


_llm_client_instance = None

def get_llm_client() -> LLMClient:
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance
