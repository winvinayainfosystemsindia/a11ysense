"""
Narrative Validation, Fix Rendering, and Template Fallback System for A11ySense AI.
Enforces plain English standards, screen reader perspectives, and developer remediation formats.
"""
import re
from typing import Dict, Any, List
from backend.common.constants.rule_catalog import RULE_CATALOG, resolve_rule
from backend.common.constants.sc_catalog import SC_CATALOG

BANNED_WORDS = [
    "aria", "dom", "attribute", "selector", "tag", "markup", "role",
    "tabindex", "node", "element id", "wcag", "axe", "semantic",
    "programmatic", "contrast ratio"
]

OLD_MOCK_SENTENCES = [
    "All interactive elements have accessible names.",
    "Element lacks accessible label.",
    "Accessibility Compliance Check",
    "Users with screen readers may struggle to understand missing labels.",
    "Add aria-label or visible text node."
]


def _count_sentences(text: str) -> int:
    """Counts sentences ending with ., ?, or !."""
    if not text or not isinstance(text, str):
        return 0
    # Clean up whitespace and split by sentence end markers
    sentences = [s.strip() for s in re.split(r'[\.\?\!]+(?:\s+|$)', text.strip()) if s.strip()]
    return len(sentences)


def _contains_banned_words(text: str) -> List[str]:
    """Checks for whole-word case-insensitive occurrences of banned words."""
    if not text or not isinstance(text, str):
        return []
    found = []
    text_lower = text.lower()
    for word in BANNED_WORDS:
        # Match whole word boundaries
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text_lower):
            found.append(word)
    return found


def validate_testcase(d: Dict[str, Any]) -> List[str]:
    """
    Validates the four testcase narrative fields.
    Returns list of problem descriptions (empty if valid).
    """
    problems = []
    required_keys = ["description", "expected_result", "actual_result", "steps_to_reproduce"]
    for key in required_keys:
        if key not in d or d[key] is None or (isinstance(d[key], str) and not d[key].strip()):
            problems.append(f"Missing or empty required key '{key}'")

    if problems:
        return problems

    desc = str(d.get("description", ""))
    expected = str(d.get("expected_result", ""))
    actual = str(d.get("actual_result", ""))
    steps = d.get("steps_to_reproduce")

    # 1. Description word count
    words = desc.split()
    if len(words) > 45:
        problems.append(f"Description exceeds 45 words ({len(words)} words)")

    # 2. Expected and Actual sentence count (2 to 4 sentences)
    exp_sent = _count_sentences(expected)
    if exp_sent < 2 or exp_sent > 4:
        problems.append(f"Expected result must be 2 to 4 sentences (found {exp_sent})")

    act_sent = _count_sentences(actual)
    if act_sent < 2 or act_sent > 4:
        problems.append(f"Actual result must be 2 to 4 sentences (found {act_sent})")

    # 3. Steps to reproduce: list of 4 to 8 non-empty strings
    if not isinstance(steps, list):
        problems.append("steps_to_reproduce must be a JSON list of strings")
    else:
        non_empty_steps = [s for s in steps if isinstance(s, str) and s.strip()]
        if len(non_empty_steps) < 4 or len(non_empty_steps) > 8:
            problems.append(f"steps_to_reproduce must contain 4 to 8 steps (found {len(non_empty_steps)})")

    # 4. Check banned words across description, expected, actual, steps
    combined_text = f"{desc} {expected} {actual} "
    if isinstance(steps, list):
        combined_text += " ".join(str(s) for s in steps)

    banned_found = _contains_banned_words(combined_text)
    if banned_found:
        problems.append(f"Contains banned words: {', '.join(set(banned_found))}")

    # 5. Check old mock sentences
    for old_s in OLD_MOCK_SENTENCES:
        if old_s.lower() in combined_text.lower():
            problems.append(f"Contains prohibited mock text: '{old_s}'")

    return problems


def validate_defect(d: Dict[str, Any]) -> List[str]:
    """
    Validates the developer-facing defect fields.
    Returns list of problem descriptions (empty if valid).
    """
    problems = []
    required_keys = [
        "friendly_name", "business_impact", "fix_steps",
        "code_before", "code_after", "verify_steps"
    ]
    for key in required_keys:
        if key not in d or d[key] is None or (isinstance(d[key], str) and not d[key].strip()):
            problems.append(f"Missing or empty required key '{key}'")

    if problems:
        return problems

    fix_steps = d.get("fix_steps")
    if not isinstance(fix_steps, list):
        problems.append("fix_steps must be a list of strings")
    else:
        valid_fix = [s for s in fix_steps if isinstance(s, str) and s.strip()]
        if len(valid_fix) < 3 or len(valid_fix) > 7:
            problems.append(f"fix_steps must contain 3 to 7 strings (found {len(valid_fix)})")

    verify_steps = d.get("verify_steps")
    if not isinstance(verify_steps, list):
        problems.append("verify_steps must be a list of strings")
    else:
        valid_verify = [s for s in verify_steps if isinstance(s, str) and s.strip()]
        if len(valid_verify) < 3 or len(valid_verify) > 5:
            problems.append(f"verify_steps must contain 3 to 5 strings (found {len(valid_verify)})")

    code_before = str(d.get("code_before", "")).strip()
    code_after = str(d.get("code_after", "")).strip()
    if not code_before:
        problems.append("code_before cannot be empty")
    if not code_after:
        problems.append("code_after cannot be empty")
    if code_before and code_after and code_before == code_after:
        problems.append("code_after must be different from code_before")

    return problems


def number_steps(steps: List[str]) -> str:
    """
    Takes a list of step strings and returns '1. …\\n2. …'.
    Strips any leading numbers the AI may have added.
    """
    if not steps or not isinstance(steps, list):
        return ""
    numbered = []
    for idx, s in enumerate(steps, start=1):
        clean_step = str(s).strip()
        # Remove leading numbers like "1.", "1)", "1 -", "Step 1:"
        clean_step = re.sub(r'^(?:step\s*)?\d+[\.\)\-:]\s*', '', clean_step, flags=re.IGNORECASE).strip()
        if clean_step:
            numbered.append(f"{idx}. {clean_step}")
    return "\n".join(numbered)


def render_fix(d: Dict[str, Any]) -> str:
    """
    Renders developer remediation section with:
    - ⚠ Verify first: (if false_positive_note)
    - How to fix: (numbered fix_steps)
    - Before: (code_before)
    - After: (code_after)
    - How to verify: (numbered verify_steps)
    """
    sections = []
    fp_note = str(d.get("false_positive_note", "")).strip()
    if fp_note:
        sections.append(f"⚠ Verify first: {fp_note}")

    fix_steps = d.get("fix_steps", [])
    if isinstance(fix_steps, list) and fix_steps:
        sections.append("How to fix:\n" + number_steps(fix_steps))

    code_before = str(d.get("code_before", "")).strip()
    if code_before:
        sections.append(f"Before:\n{code_before}")

    code_after = str(d.get("code_after", "")).strip()
    if code_after:
        sections.append(f"After:\n{code_after}")

    verify_steps = d.get("verify_steps", [])
    if isinstance(verify_steps, list) and verify_steps:
        sections.append("How to verify:\n" + number_steps(verify_steps))

    return "\n\n".join(sections)


def fallback_narrative(rule_id: str, element_ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds a deterministic, high-quality fallback narrative for an element when LLM is unavailable.
    Specific to the rule and quotes the element's visible text or label if known. Never generic.
    """
    rule_info = RULE_CATALOG.get(rule_id, {})
    sc_code = rule_info.get("sc_code") or "1.1.1"
    sc_entry = SC_CATALOG.get(sc_code, SC_CATALOG.get("1.1.1"))

    visible_text = element_ctx.get("visible_text") or element_ctx.get("accessible_name") or ""
    element_label = f"the '{visible_text}' element" if visible_text else "this element"
    plain_issue = rule_info.get("plain_issue", "does not meet accessibility requirements")

    # Description (plain English, non-technical)
    description = f"{element_label.capitalize()} {plain_issue}. This creates a barrier for people who rely on screen readers or keyboard navigation."

    # Expected result (3 parts from sc_catalog)
    expected_result = sc_entry["expected"]

    # Actual result (3 parts)
    actual_result = f"{element_label.capitalize()} {plain_issue} on this page. When a screen reader reaches this item, the user does not get the expected information or interaction. This causes confusion and slows down navigation."

    # Steps to reproduce
    page_url = element_ctx.get("page_url") or "the webpage"
    quick_key = element_ctx.get("screen_reader_quick_key", "Tab")
    steps = [
        f"Open {page_url} in your browser.",
        "Start NVDA or JAWS screen reader.",
        f"Press {quick_key} to navigate directly toward {element_label}.",
        "Listen to the announcement as focus lands on the item.",
        "Notice that the item does not announce the correct information or fails to respond properly."
    ]

    friendly_name = f"{element_label.capitalize()} {plain_issue}"[:60]
    business_impact = "Users with disabilities face navigation barriers, increasing compliance risk and reducing user satisfaction."

    html_snippet = element_ctx.get("element_html") or "<div ...></div>"
    fix_steps = [
        f"Locate {element_label} in the component template or markup.",
        "Update the element to provide clear text and proper keyboard navigation support.",
        "Ensure standard buttons or links are used instead of unlabelled generic elements.",
        "Avoid using empty labels or unannounced icon graphics."
    ]

    verify_steps = [
        "Press Tab until the element is focused and verify the focus indicator is visible.",
        "With NVDA or JAWS running, confirm the element announces its purpose clearly.",
        "Re-run the accessibility check to confirm the defect is resolved."
    ]

    return {
        "description": description,
        "expected_result": expected_result,
        "actual_result": actual_result,
        "steps_to_reproduce": steps,
        "friendly_name": friendly_name,
        "business_impact": business_impact,
        "fix_steps": fix_steps,
        "code_before": html_snippet[:300],
        "code_after": html_snippet[:300],
        "verify_steps": verify_steps,
        "false_positive_note": "",
        "remarks": "AI text unavailable: template wording used"
    }
