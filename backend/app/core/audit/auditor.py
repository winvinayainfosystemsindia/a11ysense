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
        self.testcase_prompt_template = self.load_prompt("testcases/testcase_prompt.xml")
        self.defect_prompt_template = self.load_prompt("defects/defect_prompt.xml")

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

    async def evaluate_testcase(self, context: dict, session_id: str = None) -> dict:
        """Evaluates testcase documentation using the testcase prompt template from testcases/testcase_prompt.xml."""
        prompt = self.testcase_prompt_template.format(**context)
        for attempt in range(1, 3):
            try:
                ai_response = await self.call_llm(prompt, system_message=self.system_prompt, session_id=session_id, agent_type="auditor")
                parsed = self.parse_json(ai_response)
                if "error" not in parsed:
                    return parsed
            except Exception as e:
                logger.warning(f"Testcase prompt evaluation attempt {attempt} failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(1.0)
        return {}

    async def evaluate_defect(self, context: dict, session_id: str = None) -> dict:
        """Evaluates defect documentation and remediation using the defect prompt template from defects/defect_prompt.xml."""
        prompt = self.defect_prompt_template.format(**context)
        for attempt in range(1, 3):
            try:
                ai_response = await self.call_llm(prompt, system_message=self.system_prompt, session_id=session_id, agent_type="auditor")
                parsed = self.parse_json(ai_response)
                if "error" not in parsed:
                    return parsed
            except Exception as e:
                logger.warning(f"Defect prompt evaluation attempt {attempt} failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(1.0)
        return {}

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

        context = {
            "rule_id": violation.id,
            "impact": violation.impact or "unknown",
            "description": violation.description or "",
            "help": violation.help or "",
            "help_url": violation.helpUrl or "",
            "element_selector": element_selector or "(not available)",
            "page_url": getattr(violation, "page_url", "") or "",
            "nodes_html": nodes_html if nodes_html else "(no HTML nodes captured)"
        }

        # Concurrently evaluate both testcase and defect perspectives using their separated prompts
        tc_res, def_res = await asyncio.gather(
            self.evaluate_testcase(context, session_id=session_id),
            self.evaluate_defect(context, session_id=session_id),
            return_exceptions=True
        )

        tc_data = tc_res if isinstance(tc_res, dict) else {}
        def_data = def_res if isinstance(def_res, dict) else {}

        # Cross-populate fallbacks if one succeeded and one was empty
        if not tc_data and def_data:
            tc_data = {
                "description": def_data.get("description", violation.description),
                "expected_result": def_data.get("expected_result", ""),
                "actual_result": def_data.get("actual_result", ""),
                "steps_to_reproduce": def_data.get("steps_to_reproduce", ""),
                "wcag_criteria": def_data.get("wcag_criteria", "N/A"),
                "wcag_level": def_data.get("wcag_level", "AA"),
                "wcag_principle": def_data.get("wcag_principle", "Perceivable"),
                "severity": def_data.get("severity", violation.impact or "Moderate"),
                "status": "FAIL",
                "element_html_snippet": def_data.get("element_html_snippet", nodes_html),
            }
        elif not def_data and tc_data:
            def_data = {
                "friendly_name": violation.help,
                "description": tc_data.get("description", violation.description),
                "expected_result": tc_data.get("expected_result", ""),
                "actual_result": tc_data.get("actual_result", ""),
                "steps_to_reproduce": tc_data.get("steps_to_reproduce", ""),
                "ai_fix_suggestion": "",
                "wcag_criteria": tc_data.get("wcag_criteria", "N/A"),
                "wcag_level": tc_data.get("wcag_level", "AA"),
                "wcag_principle": tc_data.get("wcag_principle", "Perceivable"),
                "severity": tc_data.get("severity", violation.impact or "Moderate"),
                "business_impact": "",
                "status": "Open",
                "element_html_snippet": tc_data.get("element_html_snippet", nodes_html),
            }

        from backend.common.constants.rule_catalog import resolve_rule
        rule_facts = resolve_rule(
            rule_id=violation.id,
            tags=getattr(violation, "tags", []),
            impact=violation.impact,
            existing_metadata=violation.metadata
        )

        # Build clean metadata structure maintaining separated testcase and defect records
        # plus backwards-compatible top-level keys.
        # WCAG criteria, level, principle, severity, status come ONLY from resolve_rule!
        violation.metadata = {
            "testcase": {
                "description": tc_data.get("description") or def_data.get("description", violation.description),
                "expected_result": tc_data.get("expected_result") or def_data.get("expected_result", ""),
                "actual_result": tc_data.get("actual_result") or def_data.get("actual_result", ""),
                "steps_to_reproduce": tc_data.get("steps_to_reproduce") or def_data.get("steps_to_reproduce", ""),
                "wcag_criteria": rule_facts["criteria"],
                "wcag_level": rule_facts["level"],
                "wcag_principle": rule_facts["principle"],
                "severity": rule_facts["severity"],
                "status": "FAIL",
                "element_html_snippet": tc_data.get("element_html_snippet") or nodes_html,
            },
            "defect": {
                "friendly_name": def_data.get("friendly_name") or violation.help,
                "description": def_data.get("description") or tc_data.get("description", violation.description),
                "expected_result": def_data.get("expected_result") or tc_data.get("expected_result", ""),
                "actual_result": def_data.get("actual_result") or tc_data.get("actual_result", ""),
                "steps_to_reproduce": def_data.get("steps_to_reproduce") or tc_data.get("steps_to_reproduce", ""),
                "ai_fix_suggestion": def_data.get("ai_fix_suggestion", ""),
                "wcag_criteria": rule_facts["criteria"],
                "wcag_level": rule_facts["level"],
                "wcag_principle": rule_facts["principle"],
                "severity": rule_facts["severity"],
                "business_impact": def_data.get("business_impact", ""),
                "status": "Open",
                "element_html_snippet": def_data.get("element_html_snippet") or nodes_html,
            },
            # Top-level backward compatibility fields
            "friendly_name": def_data.get("friendly_name", violation.help),
            "description": tc_data.get("description") or def_data.get("description", violation.description),
            "help": violation.help,
            "wcag_criteria": rule_facts["criteria"],
            "wcag_level": rule_facts["level"],
            "wcag_principle": rule_facts["principle"],
            "severity": rule_facts["severity"],
            "business_impact": def_data.get("business_impact", ""),
            "expected_result": tc_data.get("expected_result") or def_data.get("expected_result", ""),
            "actual_result": tc_data.get("actual_result") or def_data.get("actual_result", ""),
            "steps_to_reproduce": tc_data.get("steps_to_reproduce") or def_data.get("steps_to_reproduce", ""),
            "ai_fix_suggestion": def_data.get("ai_fix_suggestion", ""),
            "element_html_snippet": nodes_html,
            "remediation": def_data.get("ai_fix_suggestion", ""),
            "refined_by": "AuditorAgent",
            "input_tokens": self.last_input_tokens,
            "output_tokens": self.last_output_tokens
        }
        return violation

