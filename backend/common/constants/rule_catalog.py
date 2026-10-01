"""
Rule Catalog & WCAG Metadata Resolution for A11ySense AI.
Provides deterministic resolution of WCAG criteria, levels, principles, and severities
for both custom skills (screen_reader, keyboard_nav, landmark) and standard axe-core rules.
"""
from typing import Optional, Dict, Any, List
from backend.common.constants.wcag import WCAG_CRITERIA_MAP, parse_wcag_tags


RULE_CATALOG: Dict[str, Dict[str, Any]] = {
    # ── screen_reader.py custom rules ──────────────────────────────────────────
    "screen-reader-missing-label": {
        "sc_code": "4.1.2",
        "kind": "wcag",
        "default_severity": "Critical",
        "plain_issue": "has no accessible label",
    },
    "screen-reader-generic-label": {
        "sc_code": "2.4.6",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "has a generic label that does not describe its purpose",
    },
    "screen-reader-vague-label": {
        "sc_code": "2.4.6",
        "kind": "wcag",
        "default_severity": "Moderate",
        "plain_issue": "has a vague label that does not explain what it does",
    },
    "screen-reader-missing-dropdown-attributes": {
        "sc_code": "4.1.2",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "is missing dropdown expansion attributes",
    },
    "screen-reader-aria-role-missing-handlers": {
        "sc_code": "4.1.2",
        "kind": "wcag",
        "default_severity": "Critical",
        "plain_issue": "has an interactive role but missing click or keyboard handlers",
    },
    "screen-reader-label-in-name-mismatch": {
        "sc_code": "2.5.3",
        "kind": "wcag",
        "default_severity": "Moderate",
        "plain_issue": "accessible name does not contain its visible label",
    },
    "screen-reader-missing-landmarks": {
        "sc_code": "1.3.1",
        "kind": "wcag",
        "default_severity": "Moderate",
        "plain_issue": "content is placed outside landmark regions",
    },
    "screen-reader-broken-headings": {
        "sc_code": None,
        "kind": "best-practice",
        "default_severity": "Moderate",
        "plain_issue": "heading level hierarchy is skipped or broken",
    },
    "screen-reader-menu-missing-list-structure": {
        "sc_code": "1.3.1",
        "kind": "wcag",
        "default_severity": "Moderate",
        "plain_issue": "menu is missing proper list semantics",
    },
    "screen-reader-carousel-missing-pause": {
        "sc_code": "2.2.2",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "auto-playing carousel has no pause mechanism",
    },

    # ── keyboard_nav.py custom rules ──────────────────────────────────────────
    "keyboard-non-focusable-interactive": {
        "sc_code": "2.1.1",
        "kind": "wcag",
        "default_severity": "Critical",
        "plain_issue": "interactive element cannot be focused with keyboard",
    },
    "keyboard-trap": {
        "sc_code": "2.1.2",
        "kind": "wcag",
        "default_severity": "Critical",
        "plain_issue": "keyboard focus is trapped inside element",
    },
    "keyboard-skip-link-missing": {
        "sc_code": "2.4.1",
        "kind": "wcag",
        "default_severity": "Moderate",
        "plain_issue": "page lacks a bypass block or skip link",
    },
    "keyboard-hidden-focusable": {
        "sc_code": "2.4.7",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "focusable element is hidden offscreen or obscured",
    },
    "focus-invisible": {
        "sc_code": "2.4.7",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "focused element has no visible focus outline",
    },
    "focus-order-illogical": {
        "sc_code": "2.4.3",
        "kind": "wcag",
        "default_severity": "Moderate",
        "plain_issue": "keyboard tab navigation jumps in an illogical order",
    },
    "keyboard-dropdown-expanded-state-failure": {
        "sc_code": "4.1.2",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "dropdown toggle state does not update on keyboard activation",
    },
    "keyboard-dropdown-navigation-failure": {
        "sc_code": "2.1.1",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "dropdown menu items cannot be reached using keyboard navigation",
    },

    # ── landmark.py custom rules ─────────────────────────────────────────────
    "landmark-multiple-unlabeled": {
        "sc_code": "1.3.1",
        "kind": "wcag",
        "default_severity": "Moderate",
        "plain_issue": "multiple landmarks of same type lack distinct labels",
    },
    "landmark-duplicate-name": {
        "sc_code": "1.3.1",
        "kind": "wcag",
        "default_severity": "Moderate",
        "plain_issue": "different landmarks share identical accessible names",
    },
    "landmark-missing-name": {
        "sc_code": "1.3.1",
        "kind": "wcag",
        "default_severity": "Moderate",
        "plain_issue": "landmark region has no accessible name",
    },
    "landmark-redundant-name": {
        "sc_code": "1.3.1",
        "kind": "wcag",
        "default_severity": "Minor",
        "plain_issue": "landmark label includes redundant role name",
    },
    "landmark-generic-name": {
        "sc_code": "1.3.1",
        "kind": "wcag",
        "default_severity": "Moderate",
        "plain_issue": "landmark label is generic",
    },
}


def normalize_severity(x: Optional[str]) -> str:
    """
    Normalizes severity string to one of: Critical, Serious, Moderate, Minor.
    Maps:
      - medium / moderate -> Moderate
      - high / serious -> Serious
      - critical -> Critical
      - low / minor -> Minor
    """
    if not x:
        return "Moderate"
    val = str(x).strip().lower()
    if val in ("critical",):
        return "Critical"
    elif val in ("serious", "high"):
        return "Serious"
    elif val in ("moderate", "medium"):
        return "Moderate"
    elif val in ("minor", "low"):
        return "Minor"
    return "Moderate"


def principle_for(sc_code: Optional[str]) -> str:
    """
    Returns WCAG Principle based on the first digit of the success criterion code.
    1 -> Perceivable, 2 -> Operable, 3 -> Understandable, 4 -> Robust.
    """
    if not sc_code or not isinstance(sc_code, str):
        return "N/A"
    first = sc_code.strip()[:1]
    if first == "1":
        return "Perceivable"
    elif first == "2":
        return "Operable"
    elif first == "3":
        return "Understandable"
    elif first == "4":
        return "Robust"
    return "N/A"


def resolve_rule(
    rule_id: str,
    tags: Optional[List[str]] = None,
    impact: Optional[str] = None,
    existing_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Resolves WCAG criteria, level, principle, severity, and kind for any rule.
    Priority:
      1. Existing metadata set by the skill (if wcag_criteria is present and not N/A)
      2. RULE_CATALOG entry
      3. parse_wcag_tags(tags) for axe-core rules
      4. Best Practice fallback
    """
    meta = existing_metadata or {}
    tags = tags or []

    # 1. Existing metadata priority
    if meta.get("wcag_criteria") and meta["wcag_criteria"] not in ("N/A", ""):
        criteria = meta["wcag_criteria"]
        sc_num = criteria.split(" ")[0] if " " in criteria else criteria
        level = meta.get("wcag_level", "A")
        principle = meta.get("wcag_principle") or principle_for(sc_num)
        sev = normalize_severity(meta.get("severity") or impact)
        return {
            "criteria": criteria,
            "level": level,
            "principle": principle,
            "severity": sev,
            "kind": "wcag",
            "sc_code": sc_num
        }

    # 2. RULE_CATALOG priority
    if rule_id in RULE_CATALOG:
        entry = RULE_CATALOG[rule_id]
        sc_code = entry.get("sc_code")
        kind = entry.get("kind", "wcag")
        if sc_code and sc_code in WCAG_CRITERIA_MAP:
            criteria = WCAG_CRITERIA_MAP[sc_code]
            principle = principle_for(sc_code)
            level = "A" if sc_code in ("1.1.1", "1.2.1", "1.3.1", "2.1.1", "2.1.2", "2.4.1", "2.4.2", "2.4.4", "2.5.3", "4.1.1", "4.1.2") else "AA"
        elif kind == "best-practice" or not sc_code:
            criteria = "Best Practice"
            level = "Best Practice"
            principle = "N/A"
            kind = "best-practice"
        else:
            criteria = sc_code
            principle = principle_for(sc_code)
            level = "AA"

        sev = normalize_severity(impact or entry.get("default_severity"))
        return {
            "criteria": criteria,
            "level": level,
            "principle": principle,
            "severity": sev,
            "kind": kind,
            "sc_code": sc_code
        }

    # 3. parse_wcag_tags(tags) for axe-core rules
    has_best_practice_tag = any(t.lower() == "best-practice" for t in tags)
    criteria, level = parse_wcag_tags(tags)

    if criteria != "N/A":
        sc_num = criteria.split(" ")[0] if " " in criteria else criteria
        principle = principle_for(sc_num)
        sev = normalize_severity(impact)
        return {
            "criteria": criteria,
            "level": level,
            "principle": principle,
            "severity": sev,
            "kind": "wcag",
            "sc_code": sc_num
        }

    # If only best-practice tag or no WCAG tag present
    if has_best_practice_tag or rule_id in ("heading-order", "empty-heading", "landmark-one-main"):
        return {
            "criteria": "Best Practice",
            "level": "Best Practice",
            "principle": "N/A",
            "severity": normalize_severity(impact or "moderate"),
            "kind": "best-practice",
            "sc_code": None
        }

    # Default fallback
    return {
        "criteria": "Best Practice",
        "level": "Best Practice",
        "principle": "N/A",
        "severity": normalize_severity(impact),
        "kind": "best-practice",
        "sc_code": None
    }
