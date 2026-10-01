"""
Narrative Validation, Fix Rendering, and Template Fallback System for A11ySense AI.
Enforces plain English standards, screen reader perspectives, and developer remediation formats.
"""
import re
from typing import Dict, Any, List
from backend.common.constants.rule_catalog import RULE_CATALOG, resolve_rule
from backend.common.constants.sc_catalog import SC_CATALOG
from backend.app.core.skills.implementations.element_context import extract_context_from_html, quick_key_for

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


def fallback_narrative(rule_or_id: Any, element_ctx: Any = None) -> Dict[str, Any]:
    """
    Builds a deterministic, high-quality fallback narrative for an element when LLM is unavailable.
    Specific to the rule, quotes the element's visible text/label and parent context.
    Evaluates interactive patterns (like menu items with roving arrow keys) to distinguish
    between expected behavior (False Positive) and actual accessibility defects.
    """
    if isinstance(rule_or_id, dict):
        rule_info = rule_or_id
        rule_id = rule_info.get("id", "")
    elif isinstance(rule_or_id, str):
        rule_id = rule_or_id
        rule_info = RULE_CATALOG.get(rule_id, {})
    elif hasattr(rule_or_id, "id"):
        rule_id = getattr(rule_or_id, "id")
        rule_info = RULE_CATALOG.get(rule_id, {})
    else:
        rule_id = str(rule_or_id)
        rule_info = RULE_CATALOG.get(rule_id, {})

    html_snippet = ""
    if isinstance(element_ctx, str):
        html_snippet = element_ctx
        element_ctx = {"element_html": html_snippet}
    elif isinstance(element_ctx, dict):
        html_snippet = element_ctx.get("element_html") or element_ctx.get("html") or ""
        # Flatten nested context if present
        if isinstance(element_ctx.get("context"), dict):
            element_ctx = {**element_ctx.get("context"), **element_ctx}
    else:
        element_ctx = {}

    parsed_html_ctx = extract_context_from_html(html_snippet) if html_snippet else {}

    sc_code = rule_info.get("sc_code") or rule_info.get("wcag_sc") or "1.1.1"
    sc_entry = SC_CATALOG.get(sc_code, SC_CATALOG.get("1.1.1"))

    # Extract name, role, and parent context
    visible_text = (
        element_ctx.get("visible_text")
        or element_ctx.get("accessible_name")
        or parsed_html_ctx.get("clean_name")
        or parsed_html_ctx.get("visible_text")
        or ""
    )
    clean_name = parsed_html_ctx.get("clean_name") or visible_text or ""
    clean_name = re.sub(r',\s*(link|button|menuitem|dropdown)\s*$', '', clean_name, flags=re.IGNORECASE).strip()

    is_menu_item = (
        parsed_html_ctx.get("is_menu_item", False)
        or element_ctx.get("role") == "menuitem"
        or "menu" in str(element_ctx.get("role", "")).lower()
        or (rule_id == "keyboard-non-focusable-interactive" and "menu" in html_snippet.lower())
    )
    parent_menu = element_ctx.get("parent_menu") or ""
    page_url = element_ctx.get("page_url") or "https://lemonn.co.in/"
    quick_key = element_ctx.get("screen_reader_quick_key") or quick_key_for(element_ctx or parsed_html_ctx)
    plain_issue = rule_info.get("plain_issue", "does not meet accessibility requirements")

    # Friendly element label (non-technical)
    type_name = parsed_html_ctx.get("type_name") or ("link in the menu" if is_menu_item else "element")
    if clean_name:
        element_label = f"the '{clean_name}' {type_name}"
    else:
        element_label = f"this {type_name}"

    # ── CASE 1: Menu Items / Arrow Key Navigation Pattern ─────────────────────
    if is_menu_item or (rule_id == "keyboard-non-focusable-interactive" and is_menu_item):
        menu_desc = f"in the '{parent_menu}' menu" if parent_menu else "in the main menu"
        item_quote = f"'{clean_name}'" if clean_name else "menu"
        description = (
            f"The {item_quote} link {menu_desc} cannot be reached using the Tab key alone. "
            f"Users must test whether opening the menu and navigating with Arrow keys allows reaching and activating this link."
        )
        expected_result = (
            f"Keyboard and screen reader users should be able to open the menu and use the Arrow keys or Tab key to move to {item_quote}. "
            f"The screen reader should announce '{clean_name or 'item'}, link', and pressing Enter should open the page."
        )
        actual_result = (
            f"The {item_quote} link {menu_desc} cannot be reached using the Tab key. "
            f"Check whether pressing Down Arrow in the open menu announces '{clean_name or 'item'}, link' (Version A: Expected menu behavior / False Positive) "
            f"or if the link is completely skipped (Version B: Accessibility Issue)."
        )
        steps = [
            f"Open {page_url} in a browser.",
            "Start NVDA or JAWS screen reader.",
            f"Press Tab until you hear '{parent_menu or 'Trade & Invest'}, dropdown' or reach the navigation menu.",
            "Press Enter or Space to open the menu.",
            "Press the Down Arrow key to move through the menu items.",
            f"Listen for '{clean_name or 'item'}, link'.",
            f"Check whether you can reach the {clean_name or 'item'} link: If you can reach it using the Arrow keys -> Version A / False Positive. If the link is skipped completely -> Version B / Accessibility Issue."
        ]
        friendly_name = f"'{clean_name}' menu link navigation check"[:60]
        business_impact = f"If unreachable by keyboard, users who cannot use a mouse cannot access the {clean_name or 'item'} page from the menu, creating an accessibility barrier."
        false_pos = "Menu items are designed to be accessed using Arrow keys. Therefore, skipping them with the Tab key is expected behavior if reachable with Arrow keys."
        remarks = "Menu items are designed to be accessed using Arrow keys. Therefore, skipping them with the Tab key is expected behavior if reachable with Arrow keys."
        fix_steps = [
            f"Search the project for '{clean_name}' or href '{parsed_html_ctx.get('href', '')}' to locate the menu item.",
            "Confirm whether the menu follows the arrow key navigation pattern (roving tabindex).",
            "If it is an arrow-navigated menu, confirm that pressing Arrow Down focuses this item and Enter activates it.",
            "If it is meant to be a standard navigation link, ensure it is in the standard tab order so keyboard users can reach it."
        ]
        verify_steps = [
            "Open the parent menu and press Down Arrow to navigate to the link.",
            f"With NVDA or JAWS running, confirm the screen reader announces '{clean_name}, link'.",
            "Press Enter and verify that the page opens without needing a mouse."
        ]

    # ── CASE 2: Button Missing Label ──────────────────────────────────────────
    elif rule_id == "button-name" or (rule_info.get("sc_code") == "4.1.2" and "button" in element_label):
        description = f"{element_label.capitalize()} has no label. People who use screen readers cannot tell what action this control will perform."
        expected_result = f"{element_label.capitalize()} should have a clear label describing what it does, such as 'Search' or 'Submit'. A screen reader announces this name clearly, enabling confident self-service."
        actual_result = f"{element_label.capitalize()} announces only 'button' with no name. Users cannot tell what the button does without guessing or pressing it."
        steps = [
            f"Open {page_url} in your browser.",
            "Start NVDA or JAWS screen reader.",
            f"Press B to navigate directly to {element_label}.",
            "Listen to the announcement as focus lands on the item.",
            "Notice that the screen reader announces only 'button' without an action name."
        ]
        friendly_name = f"{element_label.capitalize()} missing accessible name"[:60]
        business_impact = "Blind users cannot tell what action this button triggers, risking accidental activation or abandoned workflows."
        false_pos = ""
        remarks = ""
        fix_steps = [
            f"Locate {element_label} in the component template.",
            "Add visible text inside the button, or provide a descriptive label for screen readers.",
            "Confirm the label clearly describes the button's action (e.g. 'Search', 'Close')."
        ]
        verify_steps = [
            "Press Tab until the button is focused.",
            "With NVDA or JAWS running, confirm the button announces its action name clearly.",
            "Activate the button with Enter or Space to confirm it performs the expected action."
        ]

    # ── CASE 3: Picture / Image Missing Alt Description ───────────────────────
    elif rule_id in ("image-alt", "input-image-alt") or (rule_info.get("sc_code") == "1.1.1" and "picture" in element_label):
        description = f"{element_label.capitalize()} has no text description. People who cannot see the picture cannot understand the information it conveys."
        expected_result = f"{element_label.capitalize()} should provide a concise text description of what it shows. The screen reader announces this description when reaching the picture, giving equal access to visual content."
        actual_result = f"{element_label.capitalize()} has no description. The screen reader announces only 'graphic' or an unreadable file name, leaving the user with missing information."
        steps = [
            f"Open {page_url} in your browser.",
            "Start NVDA or JAWS screen reader.",
            f"Press G to navigate directly to {element_label}.",
            "Listen to what the screen reader announces.",
            "Notice that you hear only 'graphic' or a file path instead of a meaningful description."
        ]
        friendly_name = f"{element_label.capitalize()} missing text description"[:60]
        business_impact = "Blind users miss visual information and branding context presented in this picture."
        false_pos = "If this picture is purely decorative background styling, it should be marked as decorative so screen readers ignore it."
        remarks = ""
        fix_steps = [
            f"Locate {element_label} in the project markup.",
            "If the picture provides information, add a short descriptive text explaining what it illustrates.",
            "If the picture is purely decorative, add an empty description (alt=\"\") so screen readers skip it."
        ]
        verify_steps = [
            "Open the page with NVDA or JAWS running.",
            "Press G to jump to the picture and verify the spoken description.",
            "Confirm the description matches the visual message accurately."
        ]

    # ── CASE 4: Form Input Missing Label ──────────────────────────────────────
    elif rule_id in ("label", "aria-input-field-name") or (rule_info.get("sc_code") in ("1.3.1", "3.3.2", "4.1.2") and "field" in element_label):
        description = f"{element_label.capitalize()} has no visible or spoken label. Users who cannot see the screen do not know what information they are asked to enter."
        expected_result = f"{element_label.capitalize()} should have a clear label explaining what to type or select. When a user tabs into the field, the screen reader announces this name along with any format requirements."
        actual_result = f"{element_label.capitalize()} has no label. The screen reader announces only 'edit' or 'combo box' without a field name, forcing the user to guess."
        steps = [
            f"Open {page_url} in your browser.",
            "Start NVDA or JAWS screen reader.",
            f"Press F to navigate directly into {element_label}.",
            "Listen to the announcement as the field receives focus.",
            "Notice that no descriptive field name is announced."
        ]
        friendly_name = f"{element_label.capitalize()} missing form label"[:60]
        business_impact = "Users cannot fill out forms or submit data without sighted assistance, causing drop-offs."
        false_pos = ""
        remarks = ""
        fix_steps = [
            f"Locate {element_label} in the form component.",
            "Add a visible <label> linked directly to this input field.",
            "Ensure the label text clearly explains what information is expected."
        ]
        verify_steps = [
            "Press Tab to focus the input field.",
            "With NVDA or JAWS running, confirm the field name is announced immediately upon focus.",
            "Type into the field and confirm the entered text is readable."
        ]

    # ── CASE 5: Color Contrast ────────────────────────────────────────────────
    elif rule_id == "color-contrast" or rule_info.get("sc_code") == "1.4.3":
        description = f"The text in {element_label} has weak contrast against its background. People with low vision or anyone reading in bright daylight cannot read it easily."
        expected_result = "Text should stand out clearly against its background with strong contrast. This ensures everyone, including people with low vision, can read words easily without eye strain."
        actual_result = f"The text in {element_label} blends into its background. The words appear faint and washed out, making reading difficult."
        steps = [
            f"Open {page_url} in your browser.",
            f"Locate {element_label} on the page.",
            "Examine the text brightness compared to the background surface.",
            "Notice that the text lacks sharp contrast and is difficult to read."
        ]
        friendly_name = f"{element_label.capitalize()} has low color contrast"[:60]
        business_impact = "People with low vision cannot read this text, reducing comprehension and accessibility compliance."
        false_pos = ""
        remarks = ""
        fix_steps = [
            f"Locate the styling rules for {element_label}.",
            "Darken the text color or lighten the background color to achieve high contrast.",
            "Verify the updated color combination under varied screen brightness settings."
        ]
        verify_steps = [
            "Visually inspect the updated text against its background.",
            "Confirm the text is crisp and readable under standard lighting.",
            "Re-scan the element to verify the contrast requirement is satisfied."
        ]

    # ── CASE 6: Spoken Label Mismatch ─────────────────────────────────────────
    elif rule_id == "screen-reader-label-in-name-mismatch" or rule_info.get("sc_code") == "2.5.3":
        name_str = clean_name or "control"
        description = f"{element_label.capitalize()} has a spoken announcement that does not match its visible text '{name_str}'. Speech-input and screen reader users cannot activate it reliably."
        expected_result = f"The spoken announcement for {element_label} must start with the visible text '{name_str}'. When a user speaks the visible words, speech-control software activates the control seamlessly."
        actual_result = f"The spoken announcement differs from the visible words '{name_str}'. People speaking the on-screen words cannot activate the control, causing frustration."
        steps = [
            f"Open {page_url} in your browser.",
            "Start NVDA or JAWS screen reader.",
            f"Navigate to {element_label}.",
            "Compare the spoken announcement with the text shown on screen.",
            f"Notice that the spoken words do not include the visible text '{name_str}'."
        ]
        friendly_name = f"{element_label.capitalize()} spoken name mismatch"[:60]
        business_impact = "Users navigating by voice commands say the visible text and the control fails to respond."
        false_pos = ""
        remarks = ""
        fix_steps = [
            f"Locate {element_label} in the component template.",
            f"Update the accessible name to begin with the exact visible text '{name_str}'.",
            "Remove unnecessary extra words that override the visible label."
        ]
        verify_steps = [
            "Navigate to the control using Tab or arrow keys.",
            f"Confirm the screen reader starts by announcing the visible text '{name_str}'.",
            "Verify speech recognition software activates the control when speaking its visible name."
        ]

    # ── DEFAULT CASE: All other rules ─────────────────────────────────────────
    else:
        description = f"{element_label.capitalize()} {plain_issue}. This creates a barrier for people who rely on screen readers or keyboard navigation."
        expected_result = sc_entry["expected"]
        actual_result = f"{element_label.capitalize()} {plain_issue} on this page. When a screen reader reaches this item, the user does not get the expected information or interaction. This causes confusion and slows down navigation."
        steps = [
            f"Open {page_url} in your browser.",
            "Start NVDA or JAWS screen reader.",
            f"Press {quick_key} to navigate directly toward {element_label}.",
            "Listen to the announcement as focus lands on the item.",
            "Notice that the item does not announce the correct information or fails to respond properly."
        ]
        friendly_name = f"{element_label.capitalize()} {plain_issue}"[:60]
        business_impact = "Users with disabilities face navigation barriers, increasing compliance risk and reducing user satisfaction."
        false_pos = ""
        remarks = ""
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
        "code_before": html_snippet[:300] if html_snippet else "<div ...></div>",
        "code_after": html_snippet[:300] if html_snippet else "<div ...></div>",
        "verify_steps": verify_steps,
        "false_positive_note": false_pos,
        "remarks": remarks
    }
