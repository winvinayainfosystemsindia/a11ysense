import io
import pytest
import openpyxl
from backend.app.core.reporting.excel_generator import generate_excel_report

def test_p5_excel_structure_and_formatting():
    sample_audit_data = {
        "task_id": "test-p5-task",
        "url": "https://example.com",
        "timestamp": "2026-10-01 12:00:00 UTC",
        "pages_scanned": ["https://example.com", "https://example.com/about"],
        "testcases": [
            {
                "testcase_id": "TC-0001",
                "defect_id": "DEF-0001",
                "rule_id": "button-name",
                "testcase_name": "Button missing text",
                "description": "=SUM(A1:A10) Formula test description",  # formula injection attempt
                "criteria": "4.1.2 Name, Role, Value",
                "level": "A",
                "principle": "Robust",
                "severity": "Critical",
                "expected_result": "Button should have name",
                "actual_result": "Button has no name",
                "steps_to_reproduce": "1. Tab to button",
                "remediation": "Add text to button",
                "business_impact": "Users blocked",
                "html_snippet": "+<button class='pay'></button>",  # formula injection attempt
                "status": "FAIL",
                "page_url": "https://example.com",
                "page_title": "Home",
                "remarks": "@admin test remarks"  # formula injection attempt
            },
            {
                "testcase_id": "TC-0002",
                "defect_id": "N/A",
                "rule_id": "image-alt",
                "testcase_name": "Image has alt text",
                "description": "Image has descriptive alt text",
                "criteria": "1.1.1 Non-text Content",
                "level": "A",
                "principle": "Perceivable",
                "severity": "N/A",
                "expected_result": "All images have text alternative",
                "actual_result": "All elements meet this requirement",
                "steps_to_reproduce": "1. Inspect image",
                "remediation": "None",
                "business_impact": "Accessible",
                "html_snippet": "<img src='logo.png' alt='Logo'>",
                "status": "PASS",
                "page_url": "https://example.com/about",
                "page_title": "About",
                "remarks": ""
            }
        ]
    }

    excel_bytes = generate_excel_report(sample_audit_data)
    assert len(excel_bytes) > 0

    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))

    # 1. Verify exact 4 sheets
    expected_sheets = ["Summary", "Test Case Report", "Defects Report", "WCAG Criteria Reference"]
    assert wb.sheetnames == expected_sheets

    # 2. Verify freeze panes on all data sheets
    for s_name in expected_sheets:
        ws = wb[s_name]
        assert ws.views.sheetView[0].showGridLines is True

    assert wb["Test Case Report"].freeze_panes == "A2"
    assert wb["Defects Report"].freeze_panes == "A2"
    assert wb["WCAG Criteria Reference"].freeze_panes == "A2"

    # 3. Verify Test Case Report has exact 14 columns
    ws_tc = wb["Test Case Report"]
    assert ws_tc.max_column == 14
    tc_headers = [ws_tc.cell(row=1, column=c).value for c in range(1, 15)]
    assert tc_headers == [
        "S.No", "Testcase ID", "Page URL", "WCAG Criteria", "Level",
        "WCAG Principle", "Element HTML Snippet", "Description",
        "Expected Result", "Actual Result", "Steps to Reproduce",
        "Status", "Severity", "Remarks"
    ]

    # Verify formula injection escaping in Test Case Report
    desc_val = ws_tc.cell(row=2, column=8).value
    assert desc_val.startswith("'=SUM"), f"Expected formula escape, got {desc_val}"
    snippet_val = ws_tc.cell(row=2, column=7).value
    assert snippet_val.startswith("'+<button"), f"Expected formula escape, got {snippet_val}"
    remarks_val = ws_tc.cell(row=2, column=14).value
    assert remarks_val.startswith("'@admin"), f"Expected formula escape, got {remarks_val}"

    # Verify Consolas 9pt on HTML snippet cell
    assert ws_tc.cell(row=2, column=7).font.name == "Consolas"
    assert ws_tc.cell(row=2, column=7).font.size == 9

    # Verify clickable hyperlink on Page URL
    url_cell = ws_tc.cell(row=2, column=3)
    assert url_cell.hyperlink is not None
    assert url_cell.hyperlink.target == "https://example.com"

    # 4. Verify Defects Report has exact 16 columns
    ws_def = wb["Defects Report"]
    assert ws_def.max_column == 16
    def_headers = [ws_def.cell(row=1, column=c).value for c in range(1, 17)]
    assert def_headers == [
        "S.No", "Defect ID", "Testcase ID", "Page URL", "WCAG Criteria",
        "Level", "WCAG Principle", "Element HTML Snippet", "Description",
        "Expected Result", "Actual Result", "Steps to Reproduce",
        "Status", "Severity", "AI Suggestion to Fix", "Remarks"
    ]

    # Exactly 1 defect for 1 FAIL testcase
    assert ws_def.max_row == 2
    assert ws_def.cell(row=2, column=2).value == "DEF-0001"
    assert ws_def.cell(row=2, column=3).value == "TC-0001"
    assert ws_def.cell(row=2, column=13).value == "Open"
    assert ws_def.cell(row=2, column=14).value == "Critical"

    # 5. Verify WCAG Criteria Reference sheet has 8 columns
    ws_wcag = wb["WCAG Criteria Reference"]
    assert ws_wcag.max_column == 8
    assert ws_wcag.max_row > 40
