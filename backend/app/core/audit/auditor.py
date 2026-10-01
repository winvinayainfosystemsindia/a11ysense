import asyncio
import os
import re
import hashlib
import logging
from typing import List, Dict, Any, Optional
from playwright.async_api import Page

from backend.app.core.audit.base import BaseAgent
from backend.app.core.skills.implementations.scanner import scanner_skill
from common.schemas.audit import AuditResult, Violation
from backend.app.core.prompts import get_testcase_prompt, get_defect_prompt, PROMPT_VERSION
from backend.common.constants.rule_catalog import resolve_rule
from backend.app.core.reporting.narrative import (
    validate_testcase,
    validate_defect,
    number_steps,
    render_fix,
    fallback_narrative
)
from backend.app.core.skills.implementations.element_context import (
    collect_element_context,
    format_element_context,
    quick_key_for
)

logger = logging.getLogger(__name__)


def compute_cache_key(rule_id: str, sc_code: str, element_html: str, prompt_kind: str) -> str:
    """Computes a sha256 cache key for an element prompt evaluation."""
    norm_html = re.sub(r'\s+', ' ', (element_html or '')).strip()
    raw = f"{PROMPT_VERSION}_{rule_id}_{sc_code}_{norm_html}_{prompt_kind}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


class AuditorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TechnicalAuditor", role="Accessibility Technical Auditor")
        self.system_prompt = "You are an accessibility expert. Follow the user's instructions exactly. Return raw JSON only."
        self._element_ai_cache: Dict[str, dict] = {}

    def apply_fallback(self, violation: Violation) -> Violation:
        """Applies a deterministic template fallback to a violation when LLM is unavailable."""
        rule_facts = resolve_rule(
            rule_id=violation.id,
            tags=getattr(violation, "tags", []),
            impact=violation.impact,
            existing_metadata=violation.metadata
        )

        nodes_html = ""
        node_ctx = {}
        if violation.nodes:
            snippets = []
            for node in violation.nodes[:3]:
                if isinstance(node, dict):
                    html = node.get("html", "")
                    if not node_ctx and node.get("context"):
                        node_ctx = node.get("context")
                else:
                    html = getattr(node, "html", "")
                    if not node_ctx and getattr(node, "context", None):
                        node_ctx = getattr(node, "context")
                if html:
                    snippets.append(html[:500])
            nodes_html = "\n".join(snippets)

        element_label = node_ctx.get("visible_text") or node_ctx.get("accessible_name") or ""
        fb_ctx = {
            "visible_text": element_label,
            "accessible_name": node_ctx.get("accessible_name", ""),
            "page_url": getattr(violation, "page_url", ""),
            "screen_reader_quick_key": quick_key_for(node_ctx),
            "element_html": nodes_html[:600]
        }
        fb = fallback_narrative(violation.id, fb_ctx)
        steps_numbered = number_steps(fb["steps_to_reproduce"])
        rendered_remediation = render_fix(fb)

        violation.metadata = {
            "testcase": {
                "description": fb["description"],
                "expected_result": fb["expected_result"],
                "actual_result": fb["actual_result"],
                "steps_to_reproduce": steps_numbered,
                "wcag_criteria": rule_facts["criteria"],
                "wcag_level": rule_facts["level"],
                "wcag_principle": rule_facts["principle"],
                "severity": rule_facts["severity"],
                "status": "FAIL",
                "element_html_snippet": nodes_html[:600],
                "remarks": "AI text unavailable: template wording used"
            },
            "defect": {
                "friendly_name": fb["friendly_name"],
                "description": fb["description"],
                "expected_result": fb["expected_result"],
                "actual_result": fb["actual_result"],
                "steps_to_reproduce": steps_numbered,
                "ai_fix_suggestion": rendered_remediation,
                "wcag_criteria": rule_facts["criteria"],
                "wcag_level": rule_facts["level"],
                "wcag_principle": rule_facts["principle"],
                "severity": rule_facts["severity"],
                "business_impact": fb["business_impact"],
                "status": "Open",
                "element_html_snippet": nodes_html[:600],
                "remarks": "AI text unavailable: template wording used",
                "fix_steps": fb["fix_steps"],
                "code_before": fb["code_before"],
                "code_after": fb["code_after"],
                "verify_steps": fb["verify_steps"],
                "false_positive_note": fb["false_positive_note"]
            },
            "friendly_name": fb["friendly_name"],
            "description": fb["description"],
            "help": violation.help,
            "wcag_criteria": rule_facts["criteria"],
            "wcag_level": rule_facts["level"],
            "wcag_principle": rule_facts["principle"],
            "severity": rule_facts["severity"],
            "business_impact": fb["business_impact"],
            "expected_result": fb["expected_result"],
            "actual_result": fb["actual_result"],
            "steps_to_reproduce": steps_numbered,
            "ai_fix_suggestion": rendered_remediation,
            "element_html_snippet": nodes_html[:600],
            "remediation": rendered_remediation,
            "refined_by": "AuditorAgent",
            "remarks": "AI text unavailable: template wording used",
            "input_tokens": 0,
            "output_tokens": 0
        }
        return violation

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

        violations = raw_violations

        # 2. Collect element context for unique nodes before LLM step (limit 3 concurrent, 2s timeout each, max 80)
        try:
            ctx_sem = asyncio.Semaphore(3)

            async def get_node_ctx(node):
                if not isinstance(node, dict) or node.get("context"):
                    return
                targets = node.get("target", [])
                if not targets:
                    return
                selector = targets[0] if isinstance(targets[0], str) else str(targets[0])
                async with ctx_sem:
                    try:
                        ctx = await asyncio.wait_for(collect_element_context(page, selector), timeout=2.0)
                        node["context"] = ctx
                    except Exception:
                        node["context"] = {}

            all_nodes = []
            for v in violations:
                if v.nodes and isinstance(v.nodes, list):
                    all_nodes.extend(v.nodes[:2])

            if all_nodes:
                await asyncio.gather(*(get_node_ctx(nd) for nd in all_nodes[:80]), return_exceptions=True)
        except Exception as e:
            logger.debug(f"Element context collection skipped/failed: {e}")

        # 3. AI Refinement (all unique elements processed under concurrency semaphore)
        to_refine = violations
        concurrency = int(os.getenv("AUDIT_LLM_CONCURRENCY", "5"))
        sem = asyncio.Semaphore(concurrency)

        async def refine_with_sem(v):
            async with sem:
                try:
                    return await self.refine_violation(v, session_id=session_id)
                except Exception as e:
                    logger.error(f"Failed to refine violation {v.id}: {str(e)}")
                    return self.apply_fallback(v)

        LLM_BATCH_TIMEOUT = int(os.environ.get("AUDIT_LLM_BATCH_TIMEOUT_SECONDS", "180"))
        try:
            refined_results = await asyncio.wait_for(
                asyncio.gather(*(refine_with_sem(v) for v in to_refine)),
                timeout=LLM_BATCH_TIMEOUT
            )
            refined_violations = list(refined_results)
        except asyncio.TimeoutError:
            logger.error(
                f"LLM refinement batch TIMED OUT after {LLM_BATCH_TIMEOUT}s on {url}. "
                "Applying fallback narrative to remaining violations."
            )
            refined_violations = []
            for v in to_refine:
                if not v.metadata or "testcase" not in v.metadata:
                    v = self.apply_fallback(v)
                refined_violations.append(v)

        logger.info(f"AuditorAgent: {len(refined_violations)} violations processed on {url}")

        # 4. Capture screenshots for refined violations
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
                            v.metadata["screenshot"] = filename
                            logger.info(f"Saved defect screenshot {filename} for rule {v.id}")
            except Exception as outer_err:
                logger.error(f"Failed in screenshot capture loop: {outer_err}")

        return refined_violations

    async def evaluate_testcase(self, context: dict, session_id: str = None) -> dict:
        """Evaluates testcase documentation using the testcase prompt template."""
        cache_k = compute_cache_key(
            context.get("rule_id", ""),
            context.get("sc_code", ""),
            context.get("element_html", ""),
            "testcase"
        )
        if cache_k in self._element_ai_cache:
            return self._element_ai_cache[cache_k]

        prompt = get_testcase_prompt(context)
        system_msg = "You are an accessibility expert. Follow the user's instructions exactly. Return raw JSON only."

        for attempt in range(1, 3):
            try:
                ai_response = await self.call_llm(prompt, system_message=system_msg, session_id=session_id, agent_type="auditor")
                parsed = self.parse_json(ai_response)
                problems = validate_testcase(parsed)
                if not problems:
                    self._element_ai_cache[cache_k] = parsed
                    return parsed

                logger.warning(f"Testcase validation failed on attempt {attempt}: {problems}")
                if attempt == 1:
                    prompt = prompt + f"\n\nYour previous answer was rejected because: {', '.join(problems)}. Fix only these problems and return the JSON again."
            except Exception as e:
                logger.warning(f"Testcase LLM call failed on attempt {attempt}: {e}")
                break

        return {}

    async def evaluate_defect(self, context: dict, session_id: str = None) -> dict:
        """Evaluates defect documentation and remediation using the defect prompt template."""
        cache_k = compute_cache_key(
            context.get("rule_id", ""),
            context.get("sc_code", ""),
            context.get("element_html", ""),
            "defect"
        )
        if cache_k in self._element_ai_cache:
            return self._element_ai_cache[cache_k]

        prompt = get_defect_prompt(context)
        system_msg = "You are an accessibility expert. Follow the user's instructions exactly. Return raw JSON only."

        for attempt in range(1, 3):
            try:
                ai_response = await self.call_llm(prompt, system_message=system_msg, session_id=session_id, agent_type="auditor")
                parsed = self.parse_json(ai_response)
                problems = validate_defect(parsed)
                if not problems:
                    self._element_ai_cache[cache_k] = parsed
                    return parsed

                logger.warning(f"Defect validation failed on attempt {attempt}: {problems}")
                if attempt == 1:
                    prompt = prompt + f"\n\nYour previous answer was rejected because: {', '.join(problems)}. Fix only these problems and return the JSON again."
            except Exception as e:
                logger.warning(f"Defect LLM call failed on attempt {attempt}: {e}")
                break

        return {}

    async def refine_violation(self, violation: Violation, session_id: str = None) -> Violation:
        """
        Refines a violation into testcase and defect perspectives using separated prompts.
        Facts (WCAG SC, level, principle, severity, status) come strictly from resolve_rule.
        """
        nodes_html = ""
        element_selector = ""
        node_ctx = {}
        if violation.nodes:
            snippets = []
            for node in violation.nodes[:3]:
                if isinstance(node, dict):
                    html = node.get("html", "")
                    targets = node.get("target", [])
                    if not node_ctx and node.get("context"):
                        node_ctx = node.get("context")
                else:
                    html = getattr(node, "html", "")
                    targets = getattr(node, "target", [])
                    if not node_ctx and getattr(node, "context", None):
                        node_ctx = getattr(node, "context")
                if html:
                    snippets.append(html[:500])
                if targets and not element_selector:
                    element_selector = targets[0] if isinstance(targets[0], str) else str(targets[0])
            nodes_html = "\n".join(snippets)

        # 1. Deterministic Rule Facts
        rule_facts = resolve_rule(
            rule_id=violation.id,
            tags=getattr(violation, "tags", []),
            impact=violation.impact,
            existing_metadata=violation.metadata
        )

        sc_code = rule_facts["sc_code"] or "1.1.1"
        sc_name = rule_facts["criteria"].split(" ", 1)[1] if " " in rule_facts["criteria"] else rule_facts["criteria"]

        formatted_ctx = format_element_context(node_ctx) if node_ctx else "(not captured)"
        quick_key = quick_key_for(node_ctx) if node_ctx else "Tab"

        tc_context = {
            "rule_id": violation.id,
            "rule_summary": violation.help or violation.id,
            "technical_description": violation.description or "",
            "sc_code": sc_code,
            "sc_name": sc_name,
            "level": rule_facts["level"],
            "principle": rule_facts["principle"],
            "severity": rule_facts["severity"],
            "page_url": getattr(violation, "page_url", "") or "",
            "page_title": getattr(violation, "page_title", "") or "",
            "current_announcement": (violation.metadata or {}).get("current_announcement", "(not captured)"),
            "element_context": formatted_ctx,
            "screen_reader_quick_key": quick_key,
            "repeat_count": str(len(violation.nodes) if violation.nodes else 1),
            "element_html": nodes_html[:600],
            "help_url": getattr(violation, "helpUrl", getattr(violation, "help_url", "")),
            "element_selector": element_selector or "(not available)"
        }

        # Step 1: Call testcase prompt first
        tc_data = await self.evaluate_testcase(tc_context, session_id=session_id)

        if not tc_data:
            # LLM failed or validation rejected: use deterministic template fallback
            fb_ctx = {
                "visible_text": node_ctx.get("visible_text", ""),
                "accessible_name": node_ctx.get("accessible_name", ""),
                "page_url": tc_context["page_url"],
                "screen_reader_quick_key": quick_key,
                "element_html": nodes_html[:600]
            }
            fb = fallback_narrative(violation.id, fb_ctx)
            tc_data = {
                "description": fb["description"],
                "expected_result": fb["expected_result"],
                "actual_result": fb["actual_result"],
                "steps_to_reproduce": fb["steps_to_reproduce"],
            }
            def_data = {
                "friendly_name": fb["friendly_name"],
                "business_impact": fb["business_impact"],
                "fix_steps": fb["fix_steps"],
                "code_before": fb["code_before"],
                "code_after": fb["code_after"],
                "verify_steps": fb["verify_steps"],
                "false_positive_note": fb["false_positive_note"],
            }
            remark = "AI text unavailable: template wording used"
        else:
            remark = ""
            # Step 2: Call defect prompt, passing validated testcase description and actual_result
            def_context = dict(tc_context)
            def_context["testcase_description"] = tc_data["description"]
            def_context["testcase_actual_result"] = tc_data["actual_result"]
            def_data = await self.evaluate_defect(def_context, session_id=session_id)
            if not def_data:
                fb_ctx = {
                    "visible_text": node_ctx.get("visible_text", ""),
                    "accessible_name": node_ctx.get("accessible_name", ""),
                    "page_url": tc_context["page_url"],
                    "screen_reader_quick_key": quick_key,
                    "element_html": nodes_html[:600]
                }
                fb = fallback_narrative(violation.id, fb_ctx)
                def_data = {
                    "friendly_name": fb["friendly_name"],
                    "business_impact": fb["business_impact"],
                    "fix_steps": fb["fix_steps"],
                    "code_before": fb["code_before"],
                    "code_after": fb["code_after"],
                    "verify_steps": fb["verify_steps"],
                    "false_positive_note": fb["false_positive_note"],
                }
                remark = "AI text unavailable: template wording used"

        rendered_remediation = render_fix(def_data)
        steps_numbered = number_steps(tc_data.get("steps_to_reproduce", []))

        violation.metadata = {
            "testcase": {
                "description": tc_data.get("description", violation.description),
                "expected_result": tc_data.get("expected_result", ""),
                "actual_result": tc_data.get("actual_result", ""),
                "steps_to_reproduce": steps_numbered,
                "wcag_criteria": rule_facts["criteria"],
                "wcag_level": rule_facts["level"],
                "wcag_principle": rule_facts["principle"],
                "severity": rule_facts["severity"],
                "status": "FAIL",
                "element_html_snippet": nodes_html[:600],
                "remarks": remark
            },
            "defect": {
                "friendly_name": def_data.get("friendly_name") or violation.help or violation.id,
                "description": tc_data.get("description", violation.description),
                "expected_result": tc_data.get("expected_result", ""),
                "actual_result": tc_data.get("actual_result", ""),
                "steps_to_reproduce": steps_numbered,
                "ai_fix_suggestion": rendered_remediation,
                "wcag_criteria": rule_facts["criteria"],
                "wcag_level": rule_facts["level"],
                "wcag_principle": rule_facts["principle"],
                "severity": rule_facts["severity"],
                "business_impact": def_data.get("business_impact", ""),
                "status": "Open",
                "element_html_snippet": nodes_html[:600],
                "remarks": remark,
                "fix_steps": def_data.get("fix_steps", []),
                "code_before": def_data.get("code_before", ""),
                "code_after": def_data.get("code_after", ""),
                "verify_steps": def_data.get("verify_steps", []),
                "false_positive_note": def_data.get("false_positive_note", "")
            },
            # Top-level backward compatibility fields
            "friendly_name": def_data.get("friendly_name") or violation.help or violation.id,
            "description": tc_data.get("description", violation.description),
            "help": violation.help,
            "wcag_criteria": rule_facts["criteria"],
            "wcag_level": rule_facts["level"],
            "wcag_principle": rule_facts["principle"],
            "severity": rule_facts["severity"],
            "business_impact": def_data.get("business_impact", ""),
            "expected_result": tc_data.get("expected_result", ""),
            "actual_result": tc_data.get("actual_result", ""),
            "steps_to_reproduce": steps_numbered,
            "ai_fix_suggestion": rendered_remediation,
            "element_html_snippet": nodes_html[:600],
            "remediation": rendered_remediation,
            "refined_by": "AuditorAgent",
            "remarks": remark,
            "input_tokens": self.last_input_tokens,
            "output_tokens": self.last_output_tokens
        }
        return violation
