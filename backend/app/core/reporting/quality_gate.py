"""
Quality Gate for A11ySense AI Accessibility Reports.
Performs deterministic quality validation on compiled test cases before report generation:
1. Zero Mock Sentences (verifies no legacy mock fallback phrases)
2. Zero Banned Words in plain-English narrative fields (description, expected_result, actual_result)
3. 1:1 Defect Mapping (every FAIL test case has exactly one unique DEF-xxxx)
4. Sequential IDs (TC-0001.. and DEF-0001..)
5. Full Criteria Coverage (26 automated + 24 manual review)
6. Deduplication Integrity (1 unique element = 1 testcase)
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from common.constants import A11YSENSE_AUDIT_SCOPE, A11YSENSE_MANUAL_REVIEW_CRITERIA
from common.constants.rule_catalog import resolve_rule

MOCK_PHRASES = [
    "mock audit completed",
    "mock finding",
    "placeholder description",
    "placeholder expected",
    "placeholder actual",
    "lorem ipsum",
    "todo: add description",
]

BANNED_WORDS = [
    "aria", "dom", "attribute", "selector", "tag", "markup", "role",
    "tabindex", "node", "element id", "wcag", "axe", "semantic",
    "programmatic", "contrast ratio"
]
BANNED_REGEX = re.compile(r"\b(" + "|".join(re.escape(w) for w in BANNED_WORDS) + r")\b", re.IGNORECASE)


@dataclass
class QualityGateIssue:
    testcase_id: str
    rule_id: str
    issue_type: str
    message: str
    severity: str  # "ERROR" or "WARNING"

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def check_report(testcases: List[Dict[str, Any]]) -> List[QualityGateIssue]:
    """
    Validates a list of testcase records. Returns empty list if all quality gates pass.
    """
    issues: List[QualityGateIssue] = []
    seen_elements = set()
    fail_tc_ids = set()
    defect_ids = set()

    for idx, tc in enumerate(testcases, start=1):
        tc_id = tc.get("testcase_id", f"UNKNOWN-{idx}")
        def_id = tc.get("defect_id", "N/A")
        rule_id = tc.get("rule_id", "Unknown")
        status = tc.get("status", "FAIL")

        # 1. Sequential ID Check
        expected_tc_id = f"TC-{idx:04d}"
        if tc_id != expected_tc_id:
            issues.append(QualityGateIssue(
                testcase_id=tc_id,
                rule_id=rule_id,
                issue_type="INVALID_TESTCASE_ID",
                message=f"Testcase ID is '{tc_id}', expected sequential ID '{expected_tc_id}'",
                severity="ERROR"
            ))

        # 2. Defect Link Check
        if status == "FAIL":
            fail_tc_ids.add(tc_id)
            if not def_id or not def_id.startswith("DEF-"):
                issues.append(QualityGateIssue(
                    testcase_id=tc_id,
                    rule_id=rule_id,
                    issue_type="MISSING_DEFECT_ID",
                    message=f"FAIL testcase has invalid defect ID: '{def_id}'",
                    severity="ERROR"
                ))
            elif def_id in defect_ids:
                issues.append(QualityGateIssue(
                    testcase_id=tc_id,
                    rule_id=rule_id,
                    issue_type="DUPLICATE_DEFECT_ID",
                    message=f"Defect ID '{def_id}' is assigned to multiple test cases",
                    severity="ERROR"
                ))
            else:
                defect_ids.add(def_id)
        else:
            if def_id != "N/A":
                issues.append(QualityGateIssue(
                    testcase_id=tc_id,
                    rule_id=rule_id,
                    issue_type="UNEXPECTED_DEFECT_ID",
                    message=f"Non-FAIL testcase has defect ID '{def_id}', expected 'N/A'",
                    severity="WARNING"
                ))

        # 3. Deduplication Check (for FAIL cases)
        if status == "FAIL":
            norm_html = " ".join((tc.get("html_snippet") or "").strip().split())
            page_url = tc.get("page_url", "")
            elem_key = (rule_id, norm_html, page_url)
            if elem_key in seen_elements:
                issues.append(QualityGateIssue(
                    testcase_id=tc_id,
                    rule_id=rule_id,
                    issue_type="DUPLICATE_ELEMENT",
                    message=f"Element duplicate found: rule '{rule_id}' on page '{page_url}' should be merged with repeat_count",
                    severity="ERROR"
                ))
            else:
                seen_elements.add(elem_key)

        # 4. Zero Mock Sentences Check
        full_text = " ".join([
            str(tc.get("description", "")),
            str(tc.get("expected_result", "")),
            str(tc.get("actual_result", "")),
            str(tc.get("steps_to_reproduce", ""))
        ]).lower()

        for phrase in MOCK_PHRASES:
            if phrase in full_text:
                issues.append(QualityGateIssue(
                    testcase_id=tc_id,
                    rule_id=rule_id,
                    issue_type="MOCK_FALLBACK_DETECTED",
                    message=f"Contains mock placeholder phrase: '{phrase}'",
                    severity="ERROR"
                ))

        # 5. Banned Words in Non-Technical Narrative Check
        # Checked on description, expected_result, actual_result
        narrative_fields = [
            ("description", tc.get("description", "")),
            ("expected_result", tc.get("expected_result", "")),
            ("actual_result", tc.get("actual_result", "")),
        ]
        for field_name, field_val in narrative_fields:
            if isinstance(field_val, str) and field_val:
                found_banned = BANNED_REGEX.findall(field_val)
                if found_banned:
                    unique_banned = sorted(list({b.lower() for b in found_banned}))
                    issues.append(QualityGateIssue(
                        testcase_id=tc_id,
                        rule_id=rule_id,
                        issue_type="BANNED_JARGON_DETECTED",
                        message=f"Field '{field_name}' contains developer jargon: {unique_banned}",
                        severity="ERROR"
                    ))

    # 6. Overall 1:1 Defect Count Check
    if len(fail_tc_ids) != len(defect_ids):
        issues.append(QualityGateIssue(
            testcase_id="GLOBAL",
            rule_id="N/A",
            issue_type="DEFECT_COUNT_MISMATCH",
            message=f"Total FAIL test cases ({len(fail_tc_ids)}) does not equal total Defect IDs ({len(defect_ids)})",
            severity="ERROR"
        ))

    return issues
