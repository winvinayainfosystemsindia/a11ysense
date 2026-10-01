"""
Unified Resilient LLM Client for A11ySense Monolith Backend.
Fallback hierarchy: Claude (Primary) -> Gemini (Fallback) -> Groq (Fallback).
Integrated with DiskCache for performance & token efficiency.
"""
import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
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


class LLMUnavailableError(Exception):
    """Raised when all configured LLM providers fail or no API keys are available."""
    def __init__(self, last_error: Optional[str] = None, tried_providers: Optional[List[str]] = None):
        self.last_error = last_error
        self.tried_providers = tried_providers or []
        super().__init__(f"All LLM providers failed. Tried: {self.tried_providers}. Last error: {self.last_error}")


class LLMClient:
    def __init__(self):
        self.default_provider = os.getenv("LLM_PROVIDER", "claude").lower()
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.cache = LLMCache()

    def health(self) -> Dict[str, str]:
        """Returns health status for each provider based on SDK installation and API key presence."""
        status = {}
        # Claude
        if not anthropic:
            status["claude"] = "SDK_MISSING"
        elif not self.anthropic_key:
            status["claude"] = "NO_KEY"
        else:
            status["claude"] = "OK"

        # Gemini
        if not genai:
            status["gemini"] = "SDK_MISSING"
        elif not self.gemini_key:
            status["gemini"] = "NO_KEY"
        else:
            status["gemini"] = "OK"

        # Groq
        if not Groq:
            status["groq"] = "SDK_MISSING"
        elif not self.groq_key:
            status["groq"] = "NO_KEY"
        else:
            status["groq"] = "OK"

        return status

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
        Raises LLMUnavailableError if all providers fail.
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
        attempted_providers = []

        for prov in providers_to_try:
            # Check availability and log reasons
            if prov == "claude":
                if not anthropic:
                    logger.warning("LLM Provider 'claude' skipped: SDK missing (anthropic package not installed)")
                    continue
                if not self.anthropic_key:
                    logger.warning("LLM Provider 'claude' skipped: API key missing (ANTHROPIC_API_KEY not set)")
                    continue
            elif prov == "gemini":
                if not genai:
                    logger.warning("LLM Provider 'gemini' skipped: SDK missing (google.generativeai not installed)")
                    continue
                if not self.gemini_key:
                    logger.warning("LLM Provider 'gemini' skipped: API key missing (GEMINI_API_KEY not set)")
                    continue
            elif prov == "groq":
                if not Groq:
                    logger.warning("LLM Provider 'groq' skipped: SDK missing (groq package not installed)")
                    continue
                if not self.groq_key:
                    logger.warning("LLM Provider 'groq' skipped: API key missing (GROQ_API_KEY not set)")
                    continue
            else:
                logger.warning(f"LLM Provider '{prov}' skipped: unknown provider")
                continue

            attempted_providers.append(prov)
            try:
                if prov == "claude":
                    result = await self._generate_claude(prompt, system_message, use_vision, image_data)
                elif prov == "gemini":
                    result = await self._generate_gemini(prompt, system_message, use_vision, image_data)
                elif prov == "groq":
                    result = await self._generate_groq(prompt, system_message)

                result["cached"] = False
                if use_cache and result.get("text"):
                    self.cache.set(prompt, result, system_message, target_provider, use_vision)
                return result

            except Exception as e:
                logger.warning(f"LLM Provider '{prov}' failed: {e}")
                last_error = str(e)
                continue

        # All providers failed or were skipped
        logger.error(f"All LLM providers failed. Tried: {attempted_providers or providers_to_try}. Last error: {last_error}")
        raise LLMUnavailableError(last_error=last_error, tried_providers=attempted_providers or providers_to_try)

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

        message = await asyncio.to_thread(client.messages.create, **kwargs)
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

        response = await asyncio.to_thread(model.generate_content, parts)
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

        kwargs = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "max_tokens": 4096
        }

        completion = await asyncio.to_thread(client.chat.completions.create, **kwargs)
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


_llm_client_instance = None

def get_llm_client() -> LLMClient:
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance
