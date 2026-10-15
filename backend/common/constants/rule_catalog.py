"""
Rule Catalog & WCAG Metadata Resolution for A11ySense AI.
Provides deterministic resolution of WCAG criteria, levels, principles, and severities
for both custom skills (screen_reader, keyboard_nav, landmark) and standard axe-core rules.
"""
import re
from typing import Optional, Dict, Any, List
try:
    from common.constants.wcag import (
        WCAG_CRITERIA_MAP, parse_wcag_tags,
        A11YSENSE_AUDIT_SCOPE, A11YSENSE_MANUAL_REVIEW_CRITERIA,
    )
except ImportError:
    from backend.common.constants.wcag import (
        WCAG_CRITERIA_MAP, parse_wcag_tags,
        A11YSENSE_AUDIT_SCOPE, A11YSENSE_MANUAL_REVIEW_CRITERIA,
    )

# Authoritative conformance level per success criterion (WCAG 2.2 A/AA set).
SC_LEVELS: Dict[str, str] = {
    c["code"]: c["level"] for c in (A11YSENSE_AUDIT_SCOPE + A11YSENSE_MANUAL_REVIEW_CRITERIA)
}
SC_LEVELS.setdefault("4.1.1", "A")


def sc_level(sc_code: Optional[str]) -> str:
    """Returns the real WCAG conformance level (A / AA) for a success criterion code."""
    return SC_LEVELS.get((sc_code or "").strip(), "AA")


# axe-core / custom-skill rules that are NOT in RULE_CATALOG, mapped to the success
# criterion they enforce. None = best practice (no WCAG success criterion).
AXE_RULE_SC: Dict[str, Optional[str]] = {
    # 4.1.2 Name, Role, Value
    "aria-prohibited-attr": "4.1.2", "aria-roles": "4.1.2", "aria-conditional-attr": "4.1.2",
    "aria-command-name": "4.1.2", "aria-dialog-name": "4.1.2", "aria-input-field-name": "4.1.2",
    "aria-toggle-field-name": "4.1.2", "aria-meter-name": "4.1.2", "aria-progressbar-name": "4.1.2",
    "aria-tooltip-name": "4.1.2", "aria-treeitem-name": "4.1.2", "aria-hidden-body": "4.1.2",
    "duplicate-id-aria": "4.1.2", "nested-interactive": "4.1.2", "input-button-name": "4.1.2",
    "select-name": "4.1.2", "frame-title": "4.1.2",
    # 1.3.1 Info and Relationships
    "aria-required-parent": "1.3.1", "aria-required-children": "1.3.1", "listitem": "1.3.1",
    "list": "1.3.1", "definition-list": "1.3.1", "dlitem": "1.3.1", "td-headers-attr": "1.3.1",
    "th-has-data-cells": "1.3.1", "td-has-header": "1.3.1",
    # 1.1.1 Non-text Content
    "role-img-alt": "1.1.1", "input-image-alt": "1.1.1", "area-alt": "1.1.1", "object-alt": "1.1.1",
    "svg-img-alt": "1.1.1", "server-side-image-map": "1.1.1",
    # Other criteria
    "html-lang-valid": "3.1.1", "html-xml-lang-mismatch": "3.1.1", "valid-lang": "3.1.2",
    "autocomplete-valid": "1.3.5", "avoid-inline-spacing": "1.4.12", "meta-viewport": "1.4.4",
    "link-in-text-block": "1.4.1", "scrollable-region-focusable": "2.1.1", "frame-focusable-content": "2.1.1",
    "form-field-multiple-labels": "3.3.2", "label-content-name-mismatch": "2.5.3",
    "video-caption": "1.2.2", "audio-caption": "1.2.1", "blink": "2.2.2", "marquee": "2.2.2",
    "meta-refresh": "2.2.1",
    # Custom skill ids
    "link-purpose": "2.4.4", "focus-order": "2.4.3", "focus-visible": "2.4.7",
    # Best practice (no WCAG success criterion)
    "region": None, "landmark-unique": None, "landmark-one-main": None, "landmark-banner-is-top-level": None,
    "landmark-contentinfo-is-top-level": None, "landmark-main-is-top-level": None,
    "landmark-no-duplicate-banner": None, "landmark-no-duplicate-contentinfo": None,
    "landmark-no-duplicate-main": None, "landmark-unique-name-pass": None, "landmark-single-pass": None,
    "page-has-heading-one": None, "skip-link": None, "tabindex": None, "accesskeys": None,
    "label-title-only": None, "image-redundant-alt": None, "presentation-role-conflict": None,
    "aria-deprecated-role": None, "aria-allowed-role": None, "meta-viewport-large": None,
    "duplicate-id": None, "scope-attr-valid": None,
}

# Plain-English problem wording for rules that have no RULE_CATALOG entry.
PLAIN_ISSUES: Dict[str, str] = {
    "aria-prohibited-attr": "uses a label or attribute that is not allowed for this kind of element",
    "region": "has content that sits outside any page landmark region",
    "landmark-unique": "shares the same landmark type and name as another landmark",
    "label-title-only": "is labelled only by a tooltip or placeholder, with no visible label",
    "aria-roles": "uses a role that does not exist",
    "aria-required-parent": "is missing the parent element its role requires",
    "aria-required-children": "is missing child elements its role requires",
    "nested-interactive": "has a clickable control placed inside another clickable control",
    "duplicate-id-aria": "shares an id with another element that is referenced by a label",
    "link-in-text-block": "is a link inside text that is only distinguished by colour",
    "avoid-inline-spacing": "blocks users from changing text spacing",
}


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

    # ── Standard axe-core rules ───────────────────────────────────────────────
    "button-name": {
        "sc_code": "4.1.2",
        "kind": "wcag",
        "default_severity": "Critical",
        "plain_issue": "button does not have a discernible text name",
    },
    "image-alt": {
        "sc_code": "1.1.1",
        "kind": "wcag",
        "default_severity": "Critical",
        "plain_issue": "image is missing an alternative text description",
    },
    "color-contrast": {
        "sc_code": "1.4.3",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "text does not have sufficient contrast against background",
    },
    "link-name": {
        "sc_code": "2.4.4",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "link has no discernible text",
    },
    "document-title": {
        "sc_code": "2.4.2",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "page does not have a title",
    },
    "html-has-lang": {
        "sc_code": "3.1.1",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "page does not specify a language",
    },
    "label": {
        "sc_code": "1.3.1",
        "kind": "wcag",
        "default_severity": "Critical",
        "plain_issue": "form element does not have a label",
    },
    "bypass": {
        "sc_code": "2.4.1",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "page lacks a mechanism to bypass repeated blocks",
    },
    "aria-allowed-attr": {
        "sc_code": "4.1.2",
        "kind": "wcag",
        "default_severity": "Critical",
        "plain_issue": "element has invalid attributes",
    },
    "aria-required-attr": {
        "sc_code": "4.1.2",
        "kind": "wcag",
        "default_severity": "Critical",
        "plain_issue": "element is missing required attributes",
    },
    "aria-valid-attr-value": {
        "sc_code": "4.1.2",
        "kind": "wcag",
        "default_severity": "Critical",
        "plain_issue": "element has an invalid attribute value",
    },
    "aria-valid-attr": {
        "sc_code": "4.1.2",
        "kind": "wcag",
        "default_severity": "Critical",
        "plain_issue": "element has an invalid attribute name",
    },
    "aria-hidden-focus": {
        "sc_code": "4.1.2",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "hidden element is focusable",
    },
    "heading-order": {
        "sc_code": None,
        "kind": "best-practice",
        "default_severity": "Moderate",
        "plain_issue": "heading level hierarchy is skipped or broken",
    },
    "empty-heading": {
        "sc_code": None,
        "kind": "best-practice",
        "default_severity": "Minor",
        "plain_issue": "heading contains no text",
    },
    "target-size": {
        "sc_code": "2.5.8",
        "kind": "wcag",
        "default_severity": "Serious",
        "plain_issue": "touch target size is too small",
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
            level = sc_level(sc_code)
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

    # 3b. Known axe/custom rule → success criterion map (used when no tags are supplied)
    if rule_id in AXE_RULE_SC and AXE_RULE_SC[rule_id]:
        sc_code = AXE_RULE_SC[rule_id]
        return {
            "criteria": WCAG_CRITERIA_MAP.get(sc_code, sc_code),
            "level": sc_level(sc_code),
            "principle": principle_for(sc_code),
            "severity": normalize_severity(impact),
            "kind": "wcag",
            "sc_code": sc_code
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


def _facts_from_code(sc_code: str) -> Dict[str, str]:
    return {
        "criteria": WCAG_CRITERIA_MAP.get(sc_code, sc_code),
        "level": sc_level(sc_code),
        "principle": principle_for(sc_code),
    }


_BEST_PRACTICE_FACTS = {"criteria": "Best Practice", "level": "Best Practice", "principle": "N/A"}


def resolve_stored_testcase(rule_id: Optional[str], testcase_name: Optional[str] = None) -> Dict[str, str]:
    """
    Re-derives WCAG criteria / level / principle for a stored test case row that has no
    persisted WCAG columns (audits created before those columns existed).
    """
    rid = (rule_id or "").strip()
    if rid.startswith("wcag-"):
        return _facts_from_code(rid[5:])
    if rid in RULE_CATALOG or rid in AXE_RULE_SC:
        facts = resolve_rule(rid)
        return {k: facts[k] for k in ("criteria", "level", "principle")}
    # PASS rows store their criteria text in testcase_name, e.g. "4.1.2 Name, Role, Value"
    m = re.match(r"^(\d\.\d\.\d+)\b", (testcase_name or "").strip())
    if m:
        return _facts_from_code(m.group(1))
    return dict(_BEST_PRACTICE_FACTS)


def wcag_fields_for_row(tc: Any) -> Dict[str, str]:
    """Returns {criteria, level, principle} for a TestCase ORM row (persisted values first)."""
    crit = getattr(tc, "wcag_criteria", None)
    if crit:
        return {
            "criteria": crit,
            "level": getattr(tc, "wcag_level", None) or "A",
            "principle": getattr(tc, "wcag_principle", None) or "N/A",
        }
    return resolve_stored_testcase(getattr(tc, "rule_id", None), getattr(tc, "testcase_name", None))

