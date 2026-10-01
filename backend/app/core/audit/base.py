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
        self.provider = os.getenv("LLM_PROVIDER", "claude").lower()
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
            logger.warning(f"Prompt file {filename} not found at {prompt_path}, using default.")
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
        Generic LLM call dispatcher using unified in-process LLMClient.
        """
        from backend.app.core.llm.client import get_llm_client
        client = get_llm_client()
        res = await client.generate(
            prompt=prompt,
            system_message=system_message,
            use_vision=use_vision,
            image_data=image_data,
            provider=self.provider
        )
        self.last_input_tokens = res.get("input_tokens", 0)
        self.last_output_tokens = res.get("output_tokens", 0)
        logger.info(f"LLM Client resolved successfully (provider={res.get('provider')}, model={res.get('model')}, cached={res.get('cached')})")
        return res.get("text", "")

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
        
        kwargs = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": content}]
        }
        if system_message and system_message.strip():
            kwargs["system"] = system_message

        message = client.messages.create(**kwargs)
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
        models = ["gemini-3.5-flash-lite", "gemini-3.5-flash"]
        last_err = None

        parts = [system_message, prompt]
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

        for model_name in models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(parts)
                text = response.text or ""

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
            except Exception as e:
                logger.warning(f"Gemini model {model_name} in base.py failed: {e}. Trying fallback...")
                last_err = e

        raise last_err or RuntimeError("All Gemini models failed")

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

    def _extract_fields_via_regex(self, text: str) -> Dict[str, Any]:
        """
        Fallback Regex parser to extract fields directly from malformed or truncated JSON.
        Supports both string fields and list fields (steps_to_reproduce, fix_steps, verify_steps).
        """
        import re
        string_fields = [
            "description", "expected_result", "actual_result",
            "friendly_name", "business_impact", "code_before",
            "code_after", "false_positive_note", "help", "remediation_plan"
        ]
        list_fields = ["steps_to_reproduce", "fix_steps", "verify_steps"]

        extracted = {}

        # 1. Extract string fields
        for field in string_fields:
            pattern = rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                val = match.group(1).replace('\\"', '"')
                extracted[field] = val

        # 2. Extract list fields
        for field in list_fields:
            list_pattern = rf'"{field}"\s*:\s*\[(.*?)\]'
            list_match = re.search(list_pattern, text, re.DOTALL)
            if list_match:
                inner = list_match.group(1)
                item_pattern = r'"((?:[^"\\]|\\.)*)"'
                items = [m.replace('\\"', '"') for m in re.findall(item_pattern, inner, re.DOTALL) if m.strip()]
                if items:
                    extracted[field] = items

        return extracted

