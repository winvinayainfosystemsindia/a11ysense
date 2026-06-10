import os
import logging
import json
from typing import Dict, Any, List
from pathlib import Path

# LLM SDKs (imported safely)
try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.provider = os.getenv("LLM_PROVIDER", "mock").lower()
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        self.skills_dir = Path(__file__).parent.parent / "skills"
        self.last_input_tokens = 0
        self.last_output_tokens = 0
        
        # API Keys
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")

    def load_prompt(self, filename: str) -> str:
        prompt_path = self.prompts_dir / filename
        if not prompt_path.exists():
            logger.warning(f"Prompt file {filename} not found, using default.")
            return f"You are a {self.role} agent named {self.name}."
        return prompt_path.read_text(encoding="utf-8")

    def load_skills_docs(self) -> str:
        """Loads all skill documentation to provide to the agent."""
        docs = []
        for md_file in self.skills_dir.glob("*.md"):
            docs.append(f"--- SKILL: {md_file.stem} ---\n{md_file.read_text(encoding='utf-8')}")
        return "\n\n".join(docs)

    async def call_llm(self, prompt: str, system_message: str = "", use_vision: bool = False, image_data: str = None, session_id: str = None, agent_type: str = None) -> str:
        """
        Generic LLM call dispatcher with centralized service routing and direct local fallback.
        """
        # Try routing to centralized LLM service
        llm_service_url = os.getenv("LLM_SERVICE_URL", "http://localhost:8005")
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                payload = {
                    "prompt": prompt,
                    "system_message": system_message,
                    "session_id": session_id,
                    "provider": self.provider,
                    "agent_type": agent_type
                }
                from common.utils.correlation import get_correlation_headers
                headers = get_correlation_headers()
                response = await client.post(f"{llm_service_url}/generate", json=payload, headers=headers, timeout=60.0)
                response.raise_for_status()
                res_data = response.json()
                self.last_input_tokens = res_data.get("input_tokens", 0)
                self.last_output_tokens = res_data.get("output_tokens", 0)
                logger.info(f"Centralized LLM Service resolved successfully (model={res_data.get('model')}, cost=${res_data.get('estimated_cost_usd')}, cached={res_data.get('cached')})")
                return res_data["text"]
        except Exception as e:
            logger.warning(f"Centralized LLM service call failed ({str(e)}). Falling back to direct local SDK clients...")

        # Local direct fallback
        if self.provider == "claude" and self.anthropic_key and anthropic:
            return await self._call_claude(prompt, system_message, use_vision, image_data)
        elif self.provider == "groq" and self.groq_key and Groq:
            return await self._call_groq(prompt, system_message)
        elif self.provider == "gemini" and self.gemini_key and genai:
            return await self._call_gemini(prompt, system_message, use_vision, image_data)
        
        self.last_input_tokens = 50
        self.last_output_tokens = 100
        return "LLM Provider not configured correctly or Mock provider active."

    async def _call_claude(self, prompt: str, system_message: str, use_vision: bool, image_data: str) -> str:
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
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620" if use_vision else "claude-3-haiku-20240307",
            max_tokens=4096,
            system=system_message,
            messages=[{"role": "user", "content": content}]
        )
        self.last_input_tokens = getattr(message.usage, "input_tokens", 0)
        self.last_output_tokens = getattr(message.usage, "output_tokens", 0)
        return message.content[0].text

    async def _call_groq(self, prompt: str, system_message: str) -> str:
        import httpx
        client = Groq(api_key=self.groq_key, http_client=httpx.Client())
        # We handle JSON parsing manually in parse_json for better resilience 
        # against markdown blocks and preamble text which can crash strict JSON mode.
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_message + "\nYou are a technical auditor. Return ONLY raw JSON data. No markdown, no preamble."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096
        )
        self.last_input_tokens = getattr(completion.usage, "prompt_tokens", 0)
        self.last_output_tokens = getattr(completion.usage, "completion_tokens", 0)
        return completion.choices[0].message.content

    async def _call_gemini(self, prompt: str, system_message: str, use_vision: bool, image_data: str) -> str:
        genai.configure(api_key=self.gemini_key)
        model_name = 'gemini-1.5-flash' if use_vision else 'gemini-1.5-pro'
        model = genai.GenerativeModel(model_name)
        
        parts = [system_message, prompt]
        if use_vision and image_data:
            parts.append({"mime_type": "image/png", "data": image_data})
            
        response = model.generate_content(parts)
        text = response.text
        
        # Read usage stats
        in_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
        out_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)
        
        # Heuristics fallback if metadata count fails
        if in_tokens == 0:
            in_tokens = len(prompt) // 4
        if out_tokens == 0:
            out_tokens = len(text) // 4
            
        self.last_input_tokens = in_tokens
        self.last_output_tokens = out_tokens
        return text

    def parse_json(self, text: str) -> Dict[str, Any]:
        """
        Parses JSON from LLM response with high resilience.
        Handles markdown blocks, truncation, and common malformations.
        Falls back to a high-fidelity Regex parser if standard JSON decoders fail.
        """
        raw_text = text  # Keep for logging
        try:
            # 1. Basic cleaning
            text = text.strip()
            
            # 2. Find the boundaries of the JSON object
            start_idx = text.find('{')
            if start_idx == -1:
                # If no opening brace, try regex extraction directly
                regex_extracted = self._extract_fields_via_regex(text)
                if regex_extracted:
                    return regex_extracted
                logger.error(f"No opening brace '{{' found in LLM response. Raw snippet: {raw_text[:500]}...")
                return {"error": "No JSON found"}

            end_idx = text.rfind('}') + 1
            
            # 3. Handle Truncation (No closing brace)
            if end_idx == 0:
                logger.warning(f"JSON appears truncated (no closing brace). Attempting recovery for: {text[start_idx:start_idx+50]}...")
                
                # Try regex extraction first on truncated string as it is much cleaner
                regex_extracted = self._extract_fields_via_regex(text)
                if regex_extracted:
                    return regex_extracted

                # Fallback to string padding recovery
                json_candidate = text[start_idx:]
                import re
                quotes = re.findall(r'(?<!\\)"', json_candidate)
                if len(quotes) % 2 != 0:
                    json_candidate += '"'
                json_candidate += "}"
                
                try:
                    return json.loads(json_candidate, strict=False)
                except Exception as e:
                    logger.error(f"JSON Recovery failed: {str(e)} | Candidate end: ...{json_candidate[-30:]}")
                    return {"error": "Truncated and unrecoverable"}

            # 4. Standard Parsing (with boundaries found)
            json_str = text[start_idx:end_idx]
            
            try:
                return json.loads(json_str, strict=False)
            except json.JSONDecodeError:
                # Try regex extraction first on decoding failure
                regex_extracted = self._extract_fields_via_regex(json_str)
                if regex_extracted:
                    return regex_extracted

                # 5. Aggressive cleaning for common LLM mistakes
                import re
                cleaned = re.sub(r':\s*`([^`]*)`(\s*[,}])', r': "\1"\2', json_str)
                cleaned = re.sub(r',\s*}', '}', cleaned)
                cleaned = re.sub(r',\s*\]', ']', cleaned)
                
                try:
                    return json.loads(cleaned, strict=False)
                except json.JSONDecodeError:
                    final_cleaned = "".join(ch for ch in cleaned if ord(ch) >= 32 or ch in '\n\r\t')
                    try:
                        return json.loads(final_cleaned, strict=False)
                    except Exception as e:
                        logger.error(f"Ultimate JSON Parse Failure: {str(e)} | Raw snippet: {raw_text[:200]}")
                        return {"error": "Critical parsing failure", "raw": raw_text}
                
        except Exception as e:
            logger.error(f"Unexpected error in parse_json: {str(e)}")
            return {"error": "Internal parser error", "raw": raw_text}

    def _extract_fields_via_regex(self, text: str) -> Dict[str, str]:
        """
        Fallback Regex parser to extract fields directly from malformed or truncated JSON.
        """
        import re
        fields = [
            "friendly_name", "wcag_criteria", "wcag_level", "severity", 
            "business_impact", "expected_result", "actual_result", 
            "steps_to_reproduce", "remediation_plan"
        ]
        extracted = {}
        for field in fields:
            # Search for standard "field": "value"
            pattern = rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                val = match.group(1)
                val = val.replace('\\"', '"')
                extracted[field] = val
            else:
                # Search for truncated "field": "value...
                pattern_trunc = rf'"{field}"\s*:\s*"(.*)'
                match_trunc = re.search(pattern_trunc, text, re.DOTALL)
                if match_trunc:
                    val = match_trunc.group(1)
                    # Stop at the next field name key
                    for other_field in fields:
                        if f'"{other_field}"' in val:
                            val = val.split(f'"{other_field}"')[0].strip()
                            val = re.sub(r'[\s",:]+$', '', val)
                            break
                    val = val.strip().rstrip('"').lstrip('"')
                    extracted[field] = val
                    
        # Return dict only if we successfully found some key fields
        if len(extracted) >= 2:
            return extracted
        return {}

