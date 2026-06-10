import asyncio
from app.agents.base import BaseAgent
from app.skills.implementations.scanner import scanner_skill
from playwright.async_api import Page
from common.schemas.audit import AuditResult, Violation
import logging
from typing import List

logger = logging.getLogger(__name__)

class AuditorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TechnicalAuditor", role="Accessibility Technical Auditor")
        self.system_prompt = self.load_prompt("auditor.xml")

    async def audit_page(
        self,
        page: Page,
        url: str,
        session_id: str = None,
        pre_scan_data: dict = None
    ) -> List[Violation]:
        """
        Runs an automated accessibility scan and then uses AI to refine the findings.
        If `pre_scan_data` is provided (already scanned by the caller), it is used
        directly to avoid a redundant second Axe evaluation on the same page.
        """
        logger.info(f"AuditorAgent scanning {url} under session {session_id}")

        # 1. Technical Scan — reuse pre-scanned data if provided
        if pre_scan_data is not None:
            scan_results = pre_scan_data
        else:
            scan_results = await scanner_skill.run_axe(page)
        raw_violations = scan_results.get("violations", [])
        
        if not raw_violations:
            logger.info(f"No violations found on {url}")
            return []

        # Use Violation objects directly from scan results
        violations = raw_violations

        # 2. AI Refinement
        refined_violations = []
        llm_refined_count = 0
        for v in violations:
            # Always refine critical keyboard navigation and screen reader simulation defects
            is_custom_defect = v.id in [
                "keyboard-trap", "focus-invisible", "focus-order-illogical",
                "screen-reader-missing-label", "screen-reader-vague-label",
                "screen-reader-missing-dropdown-attributes", "screen-reader-aria-role-missing-handlers",
                "screen-reader-label-in-name-mismatch", "screen-reader-missing-landmarks",
                "screen-reader-broken-headings", "keyboard-non-focusable-interactive",
                "keyboard-dropdown-navigation-failure", "keyboard-hidden-focusable",
                "keyboard-skip-link-missing"
            ]
            if llm_refined_count < 20 or is_custom_defect:
                try:
                    ai_refined = await self.refine_violation(v, session_id=session_id)
                    refined_violations.append(ai_refined)
                    llm_refined_count += 1
                except Exception as e:
                    logger.error(f"Failed to refine violation {v.id}: {str(e)}")
                    # Fallback to the unrefined violation so we don't lose data
                    refined_violations.append(v)
            else:
                # Keep the remaining violations unrefined rather than dropping them
                refined_violations.append(v)
            
        logger.info(f"AuditorAgent: {len(refined_violations)} violations total ({llm_refined_count} LLM-refined) on {url}")

        # 3. Capture screenshots for refined violations
        if session_id:
            try:
                from common.config import get_audit_storage_path
                import os
                import uuid
                
                reports_dir = get_audit_storage_path(session_id)
                for v in refined_violations:
                    if v.nodes:
                        first_node = v.nodes[0]
                        selector = None
                        if "target" in first_node and first_node["target"]:
                            if isinstance(first_node["target"], list):
                                selector = " >> ".join(first_node["target"])
                            else:
                                selector = first_node["target"]
                        
                        screenshot_bytes = None
                        if selector:
                            try:
                                locator = page.locator(selector).first
                                if await locator.count() > 0:
                                    await locator.scroll_into_view_if_needed(timeout=2000)
                                    await locator.evaluate("el => { el.style.outline = '3px solid #ef4444'; el.style.outlineOffset = '3px'; }")
                                    screenshot_bytes = await page.screenshot(full_page=False)
                                    await locator.evaluate("el => { el.style.outline = ''; el.style.outlineOffset = ''; }")
                            except Exception as loc_err:
                                logger.debug(f"Failed to capture highlighted screenshot for selector {selector}: {loc_err}")
                        
                        if not screenshot_bytes:
                            try:
                                screenshot_bytes = await page.screenshot(full_page=False)
                            except Exception as pg_err:
                                logger.error(f"Failed to capture fallback page screenshot: {pg_err}")
                                
                        if screenshot_bytes:
                            filename = f"screenshot_{v.id}_{uuid.uuid4().hex[:8]}.png"
                            filepath = os.path.join(reports_dir, filename)
                            with open(filepath, "wb") as f:
                                f.write(screenshot_bytes)
                            if v.metadata is None:
                                v.metadata = {}
                            v.metadata["screenshot"] = filename
                            logger.info(f"Saved defect screenshot {filename} for rule {v.id}")
            except Exception as outer_err:
                logger.error(f"Failed in screenshot capture loop: {outer_err}")

        return refined_violations

    async def refine_violation(self, violation: Violation, session_id: str = None) -> Violation:
        # Build an HTML snippet from the first 3 nodes for context
        nodes_html = ""
        if violation.nodes:
            snippets = []
            for node in violation.nodes[:3]:
                if isinstance(node, dict):
                    html = node.get("html", "")
                else:
                    html = getattr(node, "html", "")
                if html:
                    snippets.append(html[:400])
            nodes_html = "\n".join(snippets)

        prompt = f"""You are an expert Web Accessibility (WCAG 2.2) auditor writing a professional defect report entry.

TASK: Analyze the violation details below and produce a precise, clear, and professional audit report entry.

VIOLATION DATA:
- Rule ID: {violation.id}
- Impact Level: {violation.impact or "unknown"}
- Technical Description: {violation.description}
- Axe Help Text: {violation.help}
- Help URL: {violation.helpUrl}
- Affected HTML Element(s):
{nodes_html if nodes_html else "(no HTML nodes captured)"}

STRICT OUTPUT RULES:
1. Return ONLY a single raw JSON object.
2. DO NOT use markdown code blocks (```json or ```).
3. DO NOT include any text before or after the JSON.
4. All string values MUST be specific to the Rule ID "{violation.id}" — do NOT use generic image alt text examples for non-image rules.
5. Ensure double quotes inside JSON string values are escaped with backslash (\").

REQUIRED JSON FIELDS (fill each based on the ACTUAL Rule ID and HTML above):
{{
    "friendly_name": "<Clear, simple, and professional title specific to rule ID {violation.id}, easy for both developers and non-technical stakeholders to understand>",
    "description": "<Clear, professional technical description of the accessibility barrier observed>",
    "help": "<Short, actionable help text explaining how to resolve or verify this rule>",
    "wcag_criteria": "<Exact WCAG 2.2 Success Criteria ID and Name, e.g. '1.1.1 Non-text Content'>",
    "wcag_level": "<A or AA or AAA>",
    "severity": "<Critical, Serious, Moderate, or Minor — based on impact '{violation.impact}'>",
    "business_impact": "<How this specific rule violation affects users with disabilities, particularly those using assistive technologies like screen readers or keyboard navigation>",
    "expected_result": "<Specify exactly 'what it is actually' (the target compliant state/behavior) and 'how it has to be' to satisfy accessibility guidelines. Define what the element/component should announce, display, or how it should respond to keyboard interactions under standard compliance>",
    "actual_result": "<Specify exactly 'what was actually found' on the page and 'how it is currently behaving' under testing. Describe the exact failure observed in relation to the affected HTML snippet, detailing the user experience barrier>",
    "steps_to_reproduce": "<Numbered, step-by-step instructions so a developer can easily navigate, locate the exact element on the page, perform the interaction (e.g. keyboard navigation, screen reader check, inspector examination), and observe the failure>",
    "remediation_plan": "<Specific code/config fix for rule {violation.id} using semantic HTML and ARIA best practices>"
}}"""
        data = None
        for attempt in range(1, 3):
            try:
                ai_response = await self.call_llm(prompt, system_message=self.system_prompt, session_id=session_id, agent_type="auditor")
                parsed = self.parse_json(ai_response)
                
                if "error" in parsed:
                    raise ValueError(f"JSON Parse error: {parsed.get('error')}")
                
                data = parsed
                break
            except Exception as e:
                logger.warning(f"LLM refinement attempt {attempt} failed for {violation.id}: {str(e)}")
                if attempt < 2:
                    logger.info(f"Retrying LLM refinement for {violation.id} in 1 second...")
                    await asyncio.sleep(1.0)
                else:
                    logger.error(f"LLM refinement failed after {attempt} attempts for {violation.id}. Using fallback.")
                    return violation
        
        # Merge AI data into metadata
        violation.metadata = {
            "friendly_name": data.get("friendly_name", violation.help),
            "description": data.get("description", violation.description),
            "help": data.get("help", violation.help),
            "wcag_criteria": data.get("wcag_criteria", "N/A"),
            "wcag_level": data.get("wcag_level", "AA"),
            "severity": data.get("severity", violation.impact or "High"),
            "business_impact": data.get("business_impact", ""),
            "expected_result": data.get("expected_result", ""),
            "actual_result": data.get("actual_result", ""),
            "steps_to_reproduce": data.get("steps_to_reproduce", ""),
            "remediation": data.get("remediation_plan", ""),
            "refined_by": "AuditorAgent",  # Successfully refined by AuditorAgent LLM process
            "input_tokens": self.last_input_tokens,
            "output_tokens": self.last_output_tokens
        }
        return violation
