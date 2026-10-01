import asyncio
import os
from backend.app.core.audit.base import BaseAgent
from backend.app.core.skills.implementations.scanner import scanner_skill
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
        to_refine = []
        to_keep = []

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
                to_refine.append(v)
                if not is_custom_defect:
                    llm_refined_count += 1
            else:
                to_keep.append(v)

        # Run LLM refinements in parallel with a semaphore limit of 5 to avoid rate limits
        sem = asyncio.Semaphore(5)

        async def refine_with_sem(v):
            async with sem:
                try:
                    return await self.refine_violation(v, session_id=session_id)
                except Exception as e:
                    logger.error(f"Failed to refine violation {v.id}: {str(e)}")
                    # Fallback to the unrefined violation so we don't lose data
                    return v

        if to_refine:
            LLM_BATCH_TIMEOUT = int(os.environ.get("AUDIT_LLM_BATCH_TIMEOUT_SECONDS", "180"))
            try:
                refined_results = await asyncio.wait_for(
                    asyncio.gather(*(refine_with_sem(v) for v in to_refine)),
                    timeout=LLM_BATCH_TIMEOUT
                )
                refined_violations = list(refined_results) + to_keep
            except asyncio.TimeoutError:
                logger.error(
                    f"LLM refinement batch TIMED OUT after {LLM_BATCH_TIMEOUT}s on {url}. "
                    "Returning unrefined violations."
                )
                refined_violations = to_refine + to_keep
        else:
            refined_violations = to_keep

        logger.info(f"AuditorAgent: {len(refined_violations)} violations total ({len(to_refine)} LLM-refined) on {url}")

        # 3. Capture screenshots for refined violations
        if session_id:
            try:
                from common.config import get_audit_storage_path
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
        element_selector = ""
        if violation.nodes:
            snippets = []
            for node in violation.nodes[:3]:
                if isinstance(node, dict):
                    html = node.get("html", "")
                    targets = node.get("target", [])
                else:
                    html = getattr(node, "html", "")
                    targets = getattr(node, "target", [])
                if html:
                    snippets.append(html[:500])
                if targets and not element_selector:
                    element_selector = targets[0] if isinstance(targets[0], str) else str(targets[0])
            nodes_html = "\n".join(snippets)

        prompt = f"""You are a senior Web Accessibility Auditor writing a professional WCAG 2.2 compliance report for a client.

TASK: Analyse the violation below and produce ALL report fields. Your audience includes non-technical stakeholders and screen-reader users — keep the language simple, clear, and jargon-free.

VIOLATION DATA:
- Rule ID: {violation.id}
- Impact Level: {violation.impact or "unknown"}
- Technical Description: {violation.description}
- Axe Help Text: {violation.help}
- Help URL: {violation.helpUrl}
- Element Selector: {element_selector or "(not available)"}
- Affected HTML Element(s):
{nodes_html if nodes_html else "(no HTML nodes captured)"}

STRICT OUTPUT RULES:
1. Return ONLY a single raw JSON object — no markdown, no code blocks, no extra text.
2. All field values MUST be specific to this exact Rule ID "{violation.id}" and the HTML shown.
3. Do NOT invent information not supported by the data above.
4. Escape double quotes inside values with backslash.
5. "description" — Write in plain English that a non-technical person can understand. Do NOT use developer jargon. Example: instead of "Missing alt attribute on img element" write "An image on this page has no text description, so people who cannot see the image will not know what it shows."
6. "expected_result" — Tell the reader what the correct behaviour SHOULD be. Example: "Every image should have a short text description (called alt text) that explains what the image shows. When a screen reader reaches this image, it should read out this description so the user knows what the image is about."
7. "actual_result" — Tell the reader what is ACTUALLY happening right now. Example: "This image has no text description at all. When a screen reader user reaches this image, the screen reader either skips it completely or reads out the file name, which does not help the user understand the content."
8. "steps_to_reproduce" — Write numbered steps FROM THE PERSPECTIVE OF A SCREEN READER USER (NVDA / JAWS). Guide them step-by-step to find the element and observe the problem. Each step should be short and simple.
9. "ai_fix_suggestion" — Provide a step-by-step guide for the developer to fix this issue. Number each step. Include specific code changes where applicable.
10. "severity" — Must be one of: Critical, Serious, Moderate, Minor.

REQUIRED JSON FIELDS:
{{
    "friendly_name": "<Clear, simple title for this issue — understandable by anyone>",
    "description": "<Simple, non-technical explanation of what the accessibility problem is and why it matters for people with disabilities>",
    "wcag_criteria": "<Exact WCAG 2.2 Success Criteria ID and Name, e.g. '1.1.1 Non-text Content'>",
    "wcag_level": "<A or AA or AAA>",
    "severity": "<Critical, Serious, Moderate, or Minor>",
    "expected_result": "<What SHOULD happen — describe the correct, accessible behaviour in simple terms so a non-technical person understands what the element is supposed to do>",
    "actual_result": "<What IS happening right now — describe the actual barrier a user with a disability would face, referencing the specific HTML element shown above>",
    "steps_to_reproduce": "<Numbered steps (1. 2. 3. ...) written for a screen reader user (NVDA/JAWS) to navigate to the element and observe the issue. Keep each step simple and short. Start with opening the URL, then guide through keyboard/screen reader navigation to the exact element.>",
    "ai_fix_suggestion": "<Step-by-step numbered guide for the developer on how to fix this issue. Include specific HTML/ARIA code changes. Each step should be actionable.>",
    "business_impact": "<How this issue affects real users with disabilities in their daily experience>",
    "element_html_snippet": "<The exact HTML snippet of the affected element, copied from the violation data above>",
    "help": "<Short actionable guidance on what to check or fix>"
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
        
        # Merge AI data into metadata — these fields map 1:1 to the Excel report columns
        violation.metadata = {
            "friendly_name": data.get("friendly_name", violation.help),
            "description": data.get("description", violation.description),
            "help": data.get("help", violation.help),
            "wcag_criteria": data.get("wcag_criteria", "N/A"),
            "wcag_level": data.get("wcag_level", "AA"),
            "severity": data.get("severity", violation.impact or "Moderate"),
            "business_impact": data.get("business_impact", ""),
            "expected_result": data.get("expected_result", ""),
            "actual_result": data.get("actual_result", ""),
            "steps_to_reproduce": data.get("steps_to_reproduce", ""),
            "ai_fix_suggestion": data.get("ai_fix_suggestion", ""),
            "element_html_snippet": data.get("element_html_snippet", nodes_html),
            "remediation": data.get("ai_fix_suggestion", data.get("remediation_plan", "")),
            "refined_by": "AuditorAgent",
            "input_tokens": self.last_input_tokens,
            "output_tokens": self.last_output_tokens
        }
        return violation

