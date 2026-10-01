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

    def _sync_keys(self):
        """Syncs keys from environment variables dynamically."""
        env_claude = os.getenv("ANTHROPIC_API_KEY")
        if env_claude is not None:
            self.anthropic_key = env_claude
        env_gemini = os.getenv("GEMINI_API_KEY")
        if env_gemini is not None:
            self.gemini_key = env_gemini
        env_groq = os.getenv("GROQ_API_KEY")
        if env_groq is not None:
            self.groq_key = env_groq
        env_provider = os.getenv("LLM_PROVIDER")
        if env_provider is not None:
            self.default_provider = env_provider.lower()

    def health(self) -> Dict[str, str]:
        """Returns health status for each provider based on SDK installation and API key presence."""
        self._sync_keys()
        status = {}
        # Claude
        if not anthropic and not self.anthropic_key:
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
        self._sync_keys()
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
        """
        Calls Claude via Anthropic API (https://api.anthropic.com/v1/messages)
        using model 'claude-sonnet-4-6' with max_tokens 20000 and streaming support.
        """
        import httpx
        import json

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

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01"
        }
        payload = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 20000,
            "messages": [{"role": "user", "content": content}],
            "stream": True
        }
        if system_message and system_message.strip():
            payload["system"] = system_message

        try:
            async with httpx.AsyncClient(timeout=180.0) as http_client:
                async with http_client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        error_msg = error_body.decode("utf-8", errors="ignore")
                        raise RuntimeError(f"Anthropic API error (HTTP {response.status_code}): {error_msg}")

                    full_text = []
                    in_tokens = 0
                    out_tokens = 0

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if not data_str or data_str == "[DONE]":
                                continue
                            try:
                                evt = json.loads(data_str)
                                evt_type = evt.get("type")
                                if evt_type == "content_block_delta":
                                    delta = evt.get("delta", {})
                                    if delta.get("type") == "text_delta":
                                        full_text.append(delta.get("text", ""))
                                elif evt_type == "message_start":
                                    in_tokens = evt.get("message", {}).get("usage", {}).get("input_tokens", 0)
                                elif evt_type == "message_delta":
                                    out_tokens = evt.get("usage", {}).get("output_tokens", 0)
                            except Exception:
                                pass

                    text = "".join(full_text)
                    return {
                        "text": text,
                        "input_tokens": in_tokens or (len(prompt) // 4),
                        "output_tokens": out_tokens or (len(text) // 4),
                        "model": "claude-sonnet-4-6",
                        "provider": "claude"
                    }
        except Exception as e:
            logger.warning(f"Anthropic API call to https://api.anthropic.com/v1/messages failed: {e}")
            raise

    async def _generate_gemini(
        self, prompt: str, system_message: str, use_vision: bool, image_data: Optional[str]
    ) -> Dict[str, Any]:
        """
        Calls Google Gemini with failure and fallback mechanism:
        Primary: gemini-3.5-flash-lite -> Fallback: gemini-3.5-flash
        """
        genai.configure(api_key=self.gemini_key)
        models_to_try = ["gemini-3.5-flash-lite", "gemini-3.5-flash"]
        last_gemini_error = None

        parts = []
        if system_message:
            parts.append(system_message)
        parts.append(prompt)
        if use_vision and image_data:
            import base64
            if isinstance(image_data, str):
                try:
                    img_bytes = base64.b64decode(image_data)
                    parts.append({"mime_type": "image/png", "data": img_bytes})
                except Exception:
                    parts.append({"mime_type": "image/png", "data": image_data})
            else:
                parts.append({"mime_type": "image/png", "data": image_data})

        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = await asyncio.to_thread(model.generate_content, parts)
                text = response.text or ""
                in_tokens = len(prompt) // 4
                out_tokens = len(text) // 4
                try:
                    if hasattr(response, "_result") and hasattr(response._result, "usage_metadata"):
                        um = response._result.usage_metadata
                        in_tokens = getattr(um, "prompt_token_count", in_tokens)
                        out_tokens = getattr(um, "candidates_token_count", out_tokens)
                except Exception:
                    pass

                return {
                    "text": text,
                    "input_tokens": in_tokens,
                    "output_tokens": out_tokens,
                    "model": model_name,
                    "provider": "gemini"
                }
            except Exception as e:
                logger.warning(f"Gemini model '{model_name}' failed: {e}. Trying fallback model...")
                last_gemini_error = e

        raise last_gemini_error or RuntimeError("All configured Gemini models failed")

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
