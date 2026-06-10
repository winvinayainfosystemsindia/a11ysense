from app.schemas import AuditResult, Violation
from typing import List, Dict, Any
import os
import json
import logging

# LLM SDKs
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

class AgentIntelligence:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.provider = os.getenv("LLM_PROVIDER", "mock").lower()

    async def analyze_violations(self, result: AuditResult) -> AuditResult:
        """
        Refines the audit result by adding AI-powered remediation suggestions.
        """
        for violation in result.violations:
            try:
                ai_data = await self.get_ai_remediation(violation)
                violation.metadata = {
                    "friendly_name": ai_data.get("friendly_name", violation.help),
                    "remediation": ai_data.get("remediation_plan", "No plan available."),
                    "business_impact": ai_data.get("user_impact", "High impact on users."),
                    "ai_severity": ai_data.get("severity", "High")
                }
            except Exception as e:
                logger.error(f"AI Analysis failed for {violation.id}: {str(e)}")
                violation.metadata = {
                    "remediation": "AI analysis unavailable.",
                    "business_impact": "Technical scan found violation."
                }
            
        return result

    async def get_ai_remediation(self, violation: Violation) -> Dict[str, str]:
        prompt = self._build_prompt(violation)
        
        if self.provider == "groq" and self.groq_key and Groq:
            return await self._call_groq(prompt)
        elif self.provider == "claude" and self.anthropic_key and anthropic:
            return await self._call_claude(prompt)
        elif self.provider == "gemini" and self.gemini_key and genai:
            return await self._call_gemini(prompt)
        
        # Fallback to mock if no keys are provided
        return self._mock_remediation(violation)

    def _build_prompt(self, violation: Violation) -> str:
        nodes_html = "\n".join([node.get("html", "") for node in violation.nodes[:5]])
        return f"""
        You are an expert Web Accessibility (A11y) Consultant. I will provide you with a technical accessibility violation found by axe-core.
        Your job is to translate this technical data into a report that a developer can easily understand and fix.
        
        TECHNICAL DATA:
        - Violation ID: {violation.id}
        - Technical Description: {violation.description}
        - Axe Help Text: {violation.help}
        - Affected HTML: {nodes_html}
        
        Please provide your analysis in JSON format with the following fields:
        {{
            "friendly_name": "A clear, non-technical title for this issue.",
            "user_impact": "Explain exactly how this prevents a person with a specific disability (e.g., a screen reader user or someone with low vision) from using the site.",
            "remediation_plan": "A step-by-step technical instruction on how to fix this, including code examples.",
            "severity": "Critical, High, Medium, or Low based on the impact."
        }}
        """

    async def _call_groq(self, prompt: str) -> Dict[str, str]:
        if not Groq: return self._mock_remediation(None)
        import httpx
        client = Groq(api_key=self.groq_key, http_client=httpx.Client())
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)

    async def _call_claude(self, prompt: str) -> Dict[str, str]:
        client = anthropic.Anthropic(api_key=self.anthropic_key)
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        # Claude doesn't always guarantee JSON unless forced, so we parse carefully
        content = message.content[0].text
        return self._parse_json_from_text(content)

    async def _call_gemini(self, prompt: str) -> Dict[str, str]:
        genai.configure(api_key=self.gemini_key)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return self._parse_json_from_text(response.text)

    def _parse_json_from_text(self, text: str) -> Dict[str, str]:
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            return json.loads(text[start:end])
        except:
            return {"impact": "Error parsing AI response.", "fix": "Please check technical logs."}

    def _mock_remediation(self, violation: Violation) -> Dict[str, str]:
        return {
            "impact": f"This issue significantly affects users relying on assistive technologies for {violation.id}.",
            "fix": f"To fix this, ensure the element complies with {violation.help}. Refer to: {violation.helpUrl}"
        }

agent_intelligence = AgentIntelligence()
