import os
import time
import json
import logging
from typing import Dict, Any, List, Optional
import httpx

from app.schemas.llm import GenerateRequest, GenerateResponse, SessionSummaryResponse
from app.core.pricing import estimate_cost
from app.core.cache import get_redis_client

logger = logging.getLogger(__name__)

# Fallback sequence chain
FALLBACK_CHAIN = ["claude", "gemini", "mock"]

# Standard model names mapped per provider
PROVIDER_MODELS = {
    "claude": "claude-sonnet-4-6",
    "gemini": "gemini-3.5-flash-lite",
    "groq": "llama-3.1-8b-instant",
    "mock": "mock"
}

from app.repository.session_repo import session_repo

def track_session_tokens(session_id: str, provider: str, input_tokens: int, output_tokens: int, cost: float, agent_type: Optional[str] = None) -> Dict[str, Any]:
    return session_repo.track_session_tokens(session_id, provider, input_tokens, output_tokens, cost, agent_type)

def get_session_summary(session_id: str) -> SessionSummaryResponse:
    return session_repo.get_session_summary(session_id)

class CentralLLMRouter:
    def __init__(self):
        # Load API keys
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.default_provider = os.getenv("LLM_PROVIDER", "claude").lower()

    async def execute_generate(self, request: GenerateRequest) -> GenerateResponse:
        """
        Routes the generation request to the selected provider, applying caching
        checks and model-fallback loops if errors are encountered.
        """
        # Determine initial provider
        primary_provider = request.provider or self.default_provider
        if primary_provider not in FALLBACK_CHAIN:
            primary_provider = "claude" if "claude" in FALLBACK_CHAIN else "mock"
            
        # Re-arrange chain to start with primary provider
        chain = [primary_provider] + [p for p in FALLBACK_CHAIN if p != primary_provider]
        
        fallback_occurred = False
        last_error = None
        
        for idx, provider in enumerate(chain):
            try:
                # Check provider key availability before attempting API call
                if provider == "claude" and not self.anthropic_key:
                    raise ValueError("Anthropic API key is not configured")
                if provider == "gemini" and not self.gemini_key:
                    raise ValueError("Gemini API key is not configured")
                if provider == "groq" and not self.groq_key:
                    raise ValueError("Groq API key is not configured")

                # Resolve model name
                model = request.model or PROVIDER_MODELS.get(provider, "mock")
                
                # Perform call
                logger.info(f"Router calling provider: {provider} using model: {model}")
                text, in_tok, out_tok = await self._call_provider(
                    provider, model, request.prompt, request.system_message or "", request.temperature, request.max_tokens
                )
                
                # Calculate cost
                cost = estimate_cost(model, in_tok, out_tok)
                
                # Track session totals
                if request.session_id:
                    track_session_tokens(request.session_id, provider, in_tok, out_tok, cost, request.agent_type)

                    
                return GenerateResponse(
                    text=text,
                    provider=provider,
                    model=model,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    total_tokens=in_tok + out_tok,
                    estimated_cost_usd=cost,
                    fallback_occurred=fallback_occurred,
                    cached=False
                )
            except Exception as e:
                logger.warning(f"Provider {provider} failed ({str(e)}). Attempting next backup in chain...")
                fallback_occurred = True
                last_error = str(e)
                
        # If all providers fail, raise exception
        raise RuntimeError(f"All LLM central providers failed. Last error: {last_error}")

    async def _call_provider(self, provider: str, model: str, prompt: str, system: str, temp: float, max_tok: int) -> tuple[str, int, int]:
        """
        Routes execution to specific SDK handlers. Returns (text, input_tokens, output_tokens).
        """
        if provider == "groq" and self.groq_key:
            return await self._call_groq(model, prompt, system, temp, max_tok)
        elif provider == "claude" and self.anthropic_key:
            return await self._call_claude(model, prompt, system, temp, max_tok)
        elif provider == "gemini" and self.gemini_key:
            return await self._call_gemini(model, prompt, system, temp, max_tok)
        
        # Fallback Mock / Debug
        return self._call_mock(prompt)

    async def _call_groq(self, model: str, prompt: str, system: str, temp: float, max_tok: int) -> tuple[str, int, int]:
        from groq import Groq
        import httpx
        client = Groq(api_key=self.groq_key, http_client=httpx.Client())
        
        sys_msg = (system + "\n" if system else "") + "You are a technical auditor. Return ONLY raw JSON data. No markdown, no preamble."
        
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=temp,
            max_tokens=max_tok
        )
        text = completion.choices[0].message.content
        in_tokens = completion.usage.prompt_tokens
        out_tokens = completion.usage.completion_tokens
        return text, in_tokens, out_tokens

    async def _call_claude(self, model: str, prompt: str, system: str, temp: float, max_tok: int) -> tuple[str, int, int]:
        import anthropic
        client = anthropic.Anthropic(api_key=self.anthropic_key)
        
        kwargs = {
            "model": model,
            "max_tokens": max_tok,
            "temperature": temp,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system and system.strip():
            kwargs["system"] = system

        message = client.messages.create(**kwargs)
        text = message.content[0].text
        in_tokens = getattr(message.usage, "input_tokens", 0)
        out_tokens = getattr(message.usage, "output_tokens", 0)
        return text, in_tokens, out_tokens

    async def _call_gemini(self, model: str, prompt: str, system: str, temp: float, max_tok: int) -> tuple[str, int, int]:
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_key)
        gemini_model = genai.GenerativeModel(model)
        
        # Build prompt parts containing system context
        parts = [system, prompt]
        response = gemini_model.generate_content(
            parts, 
            generation_config=genai.types.GenerationConfig(
                temperature=temp,
                max_output_tokens=max_tok
            )
        )
        
        text = response.text
        
        # Read usage stats
        usage = getattr(response, "usage_metadata", None)
        in_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        out_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
        
        # Heuristics fallback if metadata count fails
        if in_tokens == 0:
            in_tokens = len(prompt) // 4
        if out_tokens == 0:
            out_tokens = len(text) // 4
            
        return text, in_tokens, out_tokens

    def _call_mock(self, prompt: str) -> tuple[str, int, int]:
        """
        Mock resolver for offline testing.
        """
        logger.info("Mock LLM generation resolving...")
        mock_response = {
            "friendly_name": "Information Hidden from Screen Readers - Missing Alternative Text",
            "description": "The page header logo image lacks a text description (alt attribute), rendering it completely hidden from screen reader users.",
            "help": "Ensure images have alternate text or a presentation role.",
            "wcag_criteria": "1.1.1 Non-text Content",
            "wcag_level": "A",
            "severity": "Critical",
            "business_impact": "Users who rely on screen readers will not receive any description of the image content or purpose, rendering it inaccessible or confusing.",
            "expected_result": "The image element MUST have a descriptive 'alt' attribute (e.g. alt='Company Logo') so that screen readers can announce its purpose. Under standard compliance, it should announce: 'Company Logo, graphic'.",
            "actual_result": "The image element <img class='logo' src='/assets/logo.png'> is missing the required 'alt' attribute. As a result, screen readers will either bypass the element or read the raw source filename, offering no meaningful description.",
            "steps_to_reproduce": "1. Open the page in the browser.\n2. Locate the logo image at the top-left corner of the page header.\n3. Navigate to the image using the keyboard or a screen reader, or inspect the DOM.\n4. Observe that the image tag lacks an alt attribute and the screen reader announces only the file path.",
            "remediation_plan": "Add a descriptive alt attribute to the image element: <img class='logo' src='/assets/logo.png' alt='Company Logo'>"
        }
        return json.dumps(mock_response), 50, 100

llm_router = CentralLLMRouter()
