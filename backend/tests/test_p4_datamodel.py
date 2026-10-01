import os
import json
import pytest
from common.schemas.audit import AuditResult, Violation
from backend.app.core.audit.orchestrator import audit_orchestrator
from common.constants import A11YSENSE_AUDIT_SCOPE, A11YSENSE_MANUAL_REVIEW_CRITERIA

@pytest.mark.asyncio
async def test_p4_multi_node_and_deduplication(tmp_path, monkeypatch):
    task_id = "test-p4-task-001"
    
    # Mock storage path to tmp_path
    monkeypatch.setattr(
        "backend.app.core.audit.orchestrator.get_audit_storage_path",
        lambda *args, **kwargs: str(tmp_path)
    )

    # 1 multi-node violation with 3 nodes:
    # 2 are identical on the same page -> should be merged to 1 TC with repeat_count=2
    # 1 is a different element on the same page -> separate TC
    v1 = Violation(
        id="button-name",
        impact="critical",
        description="Buttons must have discernible text",
        help="Buttons must have discernible text",
        nodes=[
            {"html": "<button class='btn'></button>", "target": ["button.btn"], "page_url": "https://example.com", "page_title": "Home"},
            {"html": "<button class='btn'></button>", "target": ["button.btn"], "page_url": "https://example.com", "page_title": "Home"},
            {"html": "<button class='icon-only'></button>", "target": ["button.icon-only"], "page_url": "https://example.com", "page_title": "Home"},
        ]
    )

    result = AuditResult(
        task_id=task_id,
        url="https://example.com",
        status="completed",
        violations=[v1],
        passes=[],
        metadata={"page_title": "Home"}
    )

    testcases = await audit_orchestrator.compile_and_save_testcase_report(task_id, result)

    # Verify FAIL testcases
    fail_cases = [tc for tc in testcases if tc["status"] == "FAIL"]
    assert len(fail_cases) == 2, f"Expected 2 unique fail test cases, got {len(fail_cases)}"

    # First fail test case should have repeat_count == 2
    btn1 = next(tc for tc in fail_cases if "class='btn'" in tc["html_snippet"])
    assert btn1["repeat_count"] == 2
    assert "Same problem found 2 times" in btn1["remarks"]

    # Second fail test case should have repeat_count == 1
    btn2 = next(tc for tc in fail_cases if "class='icon-only'" in tc["html_snippet"])
    assert btn2["repeat_count"] == 1
    assert btn2["remarks"] == ""

    # Verify sequential IDs
    assert fail_cases[0]["testcase_id"] == "TC-0001"
    assert fail_cases[0]["defect_id"] == "DEF-0001"
    assert fail_cases[1]["testcase_id"] == "TC-0002"
    assert fail_cases[1]["defect_id"] == "DEF-0002"

    # Verify 1:1 mapping between defect_id and testcase_id
    for fc in fail_cases:
        assert fc["defect_id"].startswith("DEF-")
        assert fc["testcase_id"].startswith("TC-")

    # Verify all non-fail cases have defect_id == "N/A"
    non_fail_cases = [tc for tc in testcases if tc["status"] != "FAIL"]
    for nfc in non_fail_cases:
        assert nfc["defect_id"] == "N/A"

    # Verify Manual Review criteria: all 24 present with Page URL == "All pages"
    manual_cases = [tc for tc in testcases if tc["status"] == "MANUAL_REVIEW"]
    assert len(manual_cases) == len(A11YSENSE_MANUAL_REVIEW_CRITERIA)
    for mc in manual_cases:
        assert mc["page_url"] == "All pages"
        assert mc["steps_to_reproduce"] != ""
        assert mc["steps_to_reproduce"] != "N/A"

    # Verify total criteria coverage (26 scope + 24 manual review)
    # The 26 scope criteria should be partitioned across FAIL, PASS, NOT_APPLICABLE
    scope_codes = {sc["code"] for sc in A11YSENSE_AUDIT_SCOPE}
    covered_scope_codes = {
        tc["criteria"].split(" ")[0] for tc in testcases if tc["status"] in ("FAIL", "PASS", "NOT_APPLICABLE")
    }
    assert scope_codes == covered_scope_codes

    # Verify file saved on disk
    saved_file = tmp_path / f"testcase_report_{task_id}.json"
    assert saved_file.exists()
    with open(saved_file, "r", encoding="utf-8") as f:
        disk_data = json.load(f)
    assert len(disk_data) == len(testcases)

    # Verify required keys in every testcase
    required_keys = [
        "testcase_id", "defect_id", "rule_id", "testcase_name", "description",
        "criteria", "level", "severity", "expected_result", "actual_result",
        "steps_to_reproduce", "remediation", "business_impact", "html_snippet",
        "status", "page_url", "page_title", "screenshot",
        # Added keys:
        "principle", "repeat_count", "remarks", "fix_steps", "code_before",
        "code_after", "verify_steps", "false_positive_note"
    ]
    for tc in disk_data:
        for k in required_keys:
            assert k in tc, f"Missing key {k} in testcase {tc.get('testcase_id')}"

@pytest.mark.asyncio
async def test_p4_pass_mode_per_criterion(tmp_path, monkeypatch):
    task_id = "test-p4-pass-mode"
    monkeypatch.setattr(
        "backend.app.core.audit.orchestrator.get_audit_storage_path",
        lambda *args, **kwargs: str(tmp_path)
    )

    # 1 pass for image-alt (SC 1.1.1)
    pass_entry = {
        "id": "image-alt",
        "nodes": [{"html": "<img src='logo.png' alt='Company Logo'>", "page_url": "https://example.com"}]
    }

    result = AuditResult(
        task_id=task_id,
        url="https://example.com",
        status="completed",
        violations=[],
        passes=[pass_entry],
        metadata={"page_title": "Home"}
    )

    # Test default mode: per_criterion
    monkeypatch.setenv("REPORT_PASS_MODE", "per_criterion")
    testcases = await audit_orchestrator.compile_and_save_testcase_report(task_id, result)

    pass_cases = [tc for tc in testcases if tc["status"] == "PASS"]
    assert len(pass_cases) == 1
    assert pass_cases[0]["criteria"].startswith("1.1.1")
    assert "All elements checked on this page meet this requirement" in pass_cases[0]["actual_result"]

@pytest.mark.asyncio
async def test_p4_reports_loads_json(tmp_path, monkeypatch):
    from backend.app.api.reports import download_excel_report
    from unittest.mock import MagicMock

    task_id = "test-p4-reports"
    sample_testcases = [
        {
            "testcase_id": "TC-0001",
            "defect_id": "DEF-0001",
            "rule_id": "button-name",
            "testcase_name": "Button missing text",
            "description": "Button has no text",
            "criteria": "4.1.2 Name, Role, Value",
            "level": "A",
            "severity": "Critical",
            "expected_result": "Button should have name",
            "actual_result": "Button has no name",
            "steps_to_reproduce": "1. Tab to button",
            "remediation": "Add text",
            "business_impact": "Users blocked",
            "html_snippet": "<button></button>",
            "status": "FAIL",
            "page_url": "https://example.com/login",
            "page_title": "Login",
            "screenshot": "N/A"
        },
        {
            "testcase_id": "TC-0002",
            "defect_id": "N/A",
            "rule_id": "image-alt",
            "testcase_name": "Image has alt",
            "description": "Image has alt",
            "criteria": "1.1.1 Non-text Content",
            "level": "A",
            "severity": "N/A",
            "expected_result": "Image has alt",
            "actual_result": "All elements meet requirement",
            "steps_to_reproduce": "1. View image",
            "remediation": "None",
            "business_impact": "Accessible",
            "html_snippet": "<img alt='logo'>",
            "status": "PASS",
            "page_url": "https://example.com/login",
            "page_title": "Login",
            "screenshot": "N/A"
        }
    ]

    async def mock_get_testcase_report(t_id):
        if t_id == task_id:
            return sample_testcases
        return []

    monkeypatch.setattr(audit_orchestrator, "get_testcase_report", mock_get_testcase_report)

    db_mock = MagicMock()
    db_mock.query.return_value.filter.return_value.first.return_value = None
    # Should not need DB records when JSON report exists
    response = await download_excel_report(task_id, db=db_mock)
    assert response.status_code == 200
    assert response.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(response.body) > 0

