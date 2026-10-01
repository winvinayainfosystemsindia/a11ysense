import pytest
from backend.app.core.reporting.quality_gate import check_report

@pytest.fixture
def valid_report_testcases():
    return [
        {
            "testcase_id": "TC-0001",
            "defect_id": "DEF-0001",
            "rule_id": "button-name",
            "testcase_name": "Button missing text",
            "description": "The button has no visible text or label. People who use screen readers cannot tell what it does.",
            "criteria": "4.1.2 Name, Role, Value",
            "level": "A",
            "principle": "Robust",
            "severity": "Critical",
            "expected_result": "Every interactive control should name its purpose clearly. When reached, the screen reader announces its name. This allows people who cannot see to make choices with confidence.",
            "actual_result": "The button has no name. When reached, nothing is spoken. This leaves users guessing.",
            "steps_to_reproduce": "1. Open the page in your browser.\n2. Start NVDA or JAWS screen reader.\n3. Press Tab to reach the button.\n4. Notice that no name is announced.",
            "remediation": "Add visible text to the button.",
            "business_impact": "Users cannot submit orders.",
            "html_snippet": "<button class='submit'></button>",
            "status": "FAIL",
            "page_url": "https://example.com/checkout",
            "page_title": "Checkout",
            "screenshot": "N/A"
        },
        {
            "testcase_id": "TC-0002",
            "defect_id": "N/A",
            "rule_id": "image-alt",
            "testcase_name": "Picture descriptions",
            "description": "Every picture has a short text description.",
            "criteria": "1.1.1 Non-text Content",
            "level": "A",
            "principle": "Perceivable",
            "severity": "N/A",
            "expected_result": "Every picture and graphic should have a short text description explaining what it shows. When a screen reader reaches the picture, it announces this text clearly. This allows people who cannot see the screen to understand the content and enjoy the full story.",
            "actual_result": "All elements checked on this page meet this requirement.",
            "steps_to_reproduce": "1. Open the page.\n2. Inspect picture descriptions.",
            "remediation": "No remediation required.",
            "business_impact": "Ensures accessible image experience.",
            "html_snippet": "N/A",
            "status": "PASS",
            "page_url": "https://example.com/checkout",
            "page_title": "Checkout",
            "screenshot": "N/A"
        }
    ]

def test_quality_gate_happy_path(valid_report_testcases):
    issues = check_report(valid_report_testcases)
    assert len(issues) == 0, f"Expected 0 issues, got {[i.message for i in issues]}"

def test_quality_gate_detects_mock_phrase(valid_report_testcases):
    corrupt = [dict(valid_report_testcases[0]), dict(valid_report_testcases[1])]
    corrupt[0]["actual_result"] = "Mock audit completed for this element."
    issues = check_report(corrupt)
    assert any(i.issue_type == "MOCK_FALLBACK_DETECTED" for i in issues)

def test_quality_gate_detects_banned_jargon(valid_report_testcases):
    corrupt = [dict(valid_report_testcases[0]), dict(valid_report_testcases[1])]
    corrupt[0]["description"] = "The element is missing aria-label attribute in the DOM markup."
    issues = check_report(corrupt)
    banned_issues = [i for i in issues if i.issue_type == "BANNED_JARGON_DETECTED"]
    assert len(banned_issues) > 0
    assert any("aria" in i.message or "attribute" in i.message for i in banned_issues)

def test_quality_gate_detects_duplicate_elements(valid_report_testcases):
    corrupt = [
        dict(valid_report_testcases[0]),
        dict(valid_report_testcases[0])  # Duplicate node on same page without repeat_count merge
    ]
    corrupt[1]["testcase_id"] = "TC-0002"
    corrupt[1]["defect_id"] = "DEF-0002"
    issues = check_report(corrupt)
    assert any(i.issue_type == "DUPLICATE_ELEMENT" for i in issues)

def test_quality_gate_detects_defect_mismatch(valid_report_testcases):
    corrupt = [dict(valid_report_testcases[0]), dict(valid_report_testcases[1])]
    corrupt[0]["defect_id"] = "N/A"  # FAIL testcase missing defect ID
    issues = check_report(corrupt)
    assert any(i.issue_type == "MISSING_DEFECT_ID" for i in issues)

def test_quality_gate_detects_non_sequential_ids(valid_report_testcases):
    corrupt = [dict(valid_report_testcases[0]), dict(valid_report_testcases[1])]
    corrupt[0]["testcase_id"] = "TC-9999"
    issues = check_report(corrupt)
    assert any(i.issue_type == "INVALID_TESTCASE_ID" for i in issues)
