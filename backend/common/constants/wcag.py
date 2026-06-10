"""
WCAG Criteria Constants
=======================
Single source of truth for all WCAG 2.x Success Criteria names and levels.

This module is imported by the agent service to dynamically resolve WCAG
criterion numbers extracted from axe-core rule tags (e.g. "wcag131" → "1.3.1").
It is intentionally decoupled from any specific rule engine so it can be
reused by any service (agent, reporting, LLM, analyzer).
"""

# Maps WCAG success criterion number → full criterion name.
# Numbers use dot notation (e.g. "1.3.1", "2.4.7").
WCAG_CRITERIA_MAP: dict[str, str] = {
    # Principle 1 – Perceivable
    "1.1.1": "1.1.1 Non-text Content",
    "1.2.1": "1.2.1 Audio-only and Video-only (Prerecorded)",
    "1.2.2": "1.2.2 Captions (Prerecorded)",
    "1.2.3": "1.2.3 Audio Description or Media Alternative (Prerecorded)",
    "1.2.4": "1.2.4 Captions (Live)",
    "1.2.5": "1.2.5 Audio Description (Prerecorded)",
    "1.2.6": "1.2.6 Sign Language (Prerecorded)",
    "1.2.7": "1.2.7 Extended Audio Description (Prerecorded)",
    "1.2.8": "1.2.8 Media Alternative (Prerecorded)",
    "1.2.9": "1.2.9 Audio-only (Live)",
    "1.3.1": "1.3.1 Info and Relationships",
    "1.3.2": "1.3.2 Meaningful Sequence",
    "1.3.3": "1.3.3 Sensory Characteristics",
    "1.3.4": "1.3.4 Orientation",
    "1.3.5": "1.3.5 Identify Input Purpose",
    "1.3.6": "1.3.6 Identify Purpose",
    "1.4.1": "1.4.1 Use of Color",
    "1.4.2": "1.4.2 Audio Control",
    "1.4.3": "1.4.3 Contrast (Minimum)",
    "1.4.4": "1.4.4 Resize Text",
    "1.4.5": "1.4.5 Images of Text",
    "1.4.6": "1.4.6 Contrast (Enhanced)",
    "1.4.7": "1.4.7 Low or No Background Audio",
    "1.4.8": "1.4.8 Visual Presentation",
    "1.4.9": "1.4.9 Images of Text (No Exception)",
    "1.4.10": "1.4.10 Reflow",
    "1.4.11": "1.4.11 Non-text Contrast",
    "1.4.12": "1.4.12 Text Spacing",
    "1.4.13": "1.4.13 Content on Hover or Focus",
    # Principle 2 – Operable
    "2.1.1": "2.1.1 Keyboard",
    "2.1.2": "2.1.2 No Keyboard Trap",
    "2.1.3": "2.1.3 Keyboard (No Exception)",
    "2.1.4": "2.1.4 Character Key Shortcuts",
    "2.2.1": "2.2.1 Timing Adjustable",
    "2.2.2": "2.2.2 Pause, Stop, Hide",
    "2.2.3": "2.2.3 No Timing",
    "2.2.4": "2.2.4 Interruptions",
    "2.2.5": "2.2.5 Re-authenticating",
    "2.2.6": "2.2.6 Timeouts",
    "2.3.1": "2.3.1 Three Flashes or Below Threshold",
    "2.3.2": "2.3.2 Three Flashes",
    "2.3.3": "2.3.3 Animation from Interactions",
    "2.4.1": "2.4.1 Bypass Blocks",
    "2.4.2": "2.4.2 Page Titled",
    "2.4.3": "2.4.3 Focus Order",
    "2.4.4": "2.4.4 Link Purpose (In Context)",
    "2.4.5": "2.4.5 Multiple Ways",
    "2.4.6": "2.4.6 Headings and Labels",
    "2.4.7": "2.4.7 Focus Visible",
    "2.4.8": "2.4.8 Location",
    "2.4.9": "2.4.9 Link Purpose (Link Only)",
    "2.4.10": "2.4.10 Section Headings",
    "2.4.11": "2.4.11 Focus Not Obscured (Minimum)",
    "2.4.12": "2.4.12 Focus Not Obscured (Enhanced)",
    "2.4.13": "2.4.13 Focus Appearance",
    "2.5.1": "2.5.1 Pointer Gestures",
    "2.5.2": "2.5.2 Pointer Cancellation",
    "2.5.3": "2.5.3 Label in Name",
    "2.5.4": "2.5.4 Motion Actuation",
    "2.5.5": "2.5.5 Target Size (Enhanced)",
    "2.5.6": "2.5.6 Concurrent Input Mechanisms",
    "2.5.7": "2.5.7 Dragging Movements",
    "2.5.8": "2.5.8 Target Size (Minimum)",
    # Principle 3 – Understandable
    "3.1.1": "3.1.1 Language of Page",
    "3.1.2": "3.1.2 Language of Parts",
    "3.1.3": "3.1.3 Unusual Words",
    "3.1.4": "3.1.4 Abbreviations",
    "3.1.5": "3.1.5 Reading Level",
    "3.1.6": "3.1.6 Pronunciation",
    "3.2.1": "3.2.1 On Focus",
    "3.2.2": "3.2.2 On Input",
    "3.2.3": "3.2.3 Consistent Navigation",
    "3.2.4": "3.2.4 Consistent Identification",
    "3.2.5": "3.2.5 Change on Request",
    "3.2.6": "3.2.6 Consistent Help",
    "3.3.1": "3.3.1 Error Identification",
    "3.3.2": "3.3.2 Labels or Instructions",
    "3.3.3": "3.3.3 Error Suggestion",
    "3.3.4": "3.3.4 Error Prevention (Legal, Financial, Data)",
    "3.3.5": "3.3.5 Help",
    "3.3.6": "3.3.6 Error Prevention (All)",
    "3.3.7": "3.3.7 Redundant Entry",
    "3.3.8": "3.3.8 Accessible Authentication (Minimum)",
    "3.3.9": "3.3.9 Accessible Authentication (Enhanced)",
    # Principle 4 – Robust
    "4.1.1": "4.1.1 Parsing",
    "4.1.2": "4.1.2 Name, Role, Value",
    "4.1.3": "4.1.3 Status Messages",
}

# Impact level → WCAG conformance level mapping used when deriving level
# for custom skill passes that don't carry axe-core tags.
IMPACT_TO_LEVEL: dict[str, str] = {
    "critical": "A",
    "serious": "A",
    "moderate": "AA",
    "minor": "AA",
}

# Impact level → human-readable severity (capitalised) for display.
IMPACT_TO_SEVERITY: dict[str, str] = {
    "critical": "Critical",
    "serious": "Serious",
    "moderate": "Moderate",
    "minor": "Minor",
}


def parse_wcag_tags(tags: list[str]) -> tuple[str, str]:
    """
    Parse axe-core rule tags to extract WCAG criteria and conformance level.

    axe-core embeds tags like ``wcag2a``, ``wcag2aa``, ``wcag2aaa`` for the
    conformance level and tags like ``wcag131``, ``wcag143`` for the specific
    criterion number.

    Returns
    -------
    (criteria, level) : (str, str)
        e.g. ("1.4.3 Contrast (Minimum)", "AA"), or ("N/A", "N/A") when
        no WCAG tags are present.
    """
    criteria = "N/A"
    level = "N/A"

    for tag in tags or []:
        tag_lower = tag.lower()

        # Determine conformance level from level tags (match longest first)
        if tag_lower in ("wcag2aaa", "wcag21aaa", "wcag22aaa"):
            level = "AAA"
        elif tag_lower in ("wcag2aa", "wcag21aa", "wcag22aa"):
            if level != "AAA":
                level = "AA"
        elif tag_lower in ("wcag2a", "wcag21a", "wcag22a"):
            if level not in ("AA", "AAA"):
                level = "A"

        # Extract criterion number from tags like wcag131, wcag1410, wcag247
        if tag_lower.startswith("wcag") and len(tag_lower) > 4:
            suffix = tag_lower[4:]
            # Only process pure numeric suffixes (criterion tags, not level tags)
            if suffix.isdigit() and len(suffix) >= 3:
                formatted = _format_criterion(suffix)
                if formatted in WCAG_CRITERIA_MAP:
                    criteria = WCAG_CRITERIA_MAP[formatted]

    return criteria, level


def _format_criterion(digits: str) -> str:
    """
    Convert a run of digits from an axe tag into dot-notation.

    Examples
    --------
    "131"  → "1.3.1"
    "1410" → "1.4.10"
    "247"  → "2.4.7"
    "211"  → "2.1.1"
    """
    # Handle 4-digit criteria (e.g. 1.4.10 = "1410", 2.4.11 = "2411")
    if len(digits) == 4:
        # First digit is principle, second is guideline, last two are criterion
        return f"{digits[0]}.{digits[1]}.{digits[2:]}"
    # Standard 3-digit criteria (e.g. 1.3.1 = "131")
    if len(digits) == 3:
        return f"{digits[0]}.{digits[1]}.{digits[2]}"
    return digits
