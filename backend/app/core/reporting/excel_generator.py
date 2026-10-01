"""
Excel Report Generator for A11ySense AI.
Generates an executive 3-sheet workbook:
1. Defect Report (Dark Red #8B0000)
2. Test Case Report (Dark Blue #1a237e)
3. WCAG Criteria Reference (Light Blue #1565c0)
"""
import io
import logging
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from common.constants.wcag import WCAG_CRITERIA_MAP

logger = logging.getLogger(__name__)

# Colors
DARK_RED_FILL = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
DARK_BLUE_FILL = PatternFill(start_color="1A237E", end_color="1A237E", fill_type="solid")
LIGHT_BLUE_FILL = PatternFill(start_color="1565C0", end_color="1565C0", fill_type="solid")

WHITE_BOLD_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
REGULAR_FONT = Font(name="Calibri", size=10)
BOLD_FONT = Font(name="Calibri", size=10, bold=True)

PASS_FILL = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
PASS_FONT = Font(name="Calibri", size=10, color="2E7D32", bold=True)
FAIL_FILL = PatternFill(start_color="FFEBEE", end_color="FFEBEE", fill_type="solid")
FAIL_FONT = Font(name="Calibri", size=10, color="C62828", bold=True)

THIN_BORDER = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC")
)

def build_wcag_principle(sc_code: str) -> str:
    """Derive WCAG principle (Perceivable, Operable, Understandable, Robust)."""
    if sc_code.startswith("1."):
        return "Perceivable"
    elif sc_code.startswith("2."):
        return "Operable"
    elif sc_code.startswith("3."):
        return "Understandable"
    elif sc_code.startswith("4."):
        return "Robust"
    return "General"

def generate_excel_report(audit_data: Dict[str, Any]) -> bytes:
    """
    Generates Excel report binary (.xlsx) with 3 sheets matching specific user templates.
    """
    wb = openpyxl.Workbook()
    # Remove default sheet
    default_sheet = wb.active

    violations = audit_data.get("violations", [])
    passes = audit_data.get("passes", [])
    pages = audit_data.get("pages_scanned", [])

    # ==========================================
    # SHEET 1: Defect Report (Red Header)
    # ==========================================
    ws_defects = wb.create_sheet(title="Defect Report")
    defect_headers = [
        "S.No", "Defect ID", "Page URL", "Menu Name", "Component Name",
        "WCAG Criteria", "Level", "WCAG Principle", "Impact / Severity",
        "Expected Result", "Actual Result", "Description", "Steps to Reproduce", "Remediation Plan"
    ]
    ws_defects.append(defect_headers)
    for col_idx in range(1, len(defect_headers) + 1):
        cell = ws_defects.cell(row=1, column=col_idx)
        cell.fill = DARK_RED_FILL
        cell.font = WHITE_BOLD_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    defect_row_idx = 2
    for idx, v in enumerate(violations, start=1):
        sc_info = v.get("wcag_criteria", v.get("rule_id", "N/A"))
        sc_num = sc_info.split(" ")[0] if " " in str(sc_info) else str(sc_info)
        principle = build_wcag_principle(sc_num)
        
        row_data = [
            idx,
            f"DEF-{idx:03d}",
            v.get("page_url", v.get("url", "N/A")),
            v.get("menu_name", v.get("page_title", "Page Section")),
            v.get("component_name", v.get("target_selector", "UI Element")),
            v.get("wcag_criteria", "1.1.1 Non-text Content"),
            v.get("wcag_level", "A"),
            principle,
            v.get("impact", v.get("severity", "Moderate")).capitalize(),
            v.get("expected_result", "The element MUST conform to WCAG 2.2 accessibility standards."),
            v.get("actual_result", v.get("help", "Element violates accessibility criteria.")),
            v.get("description", "Accessibility violation detected."),
            v.get("steps_to_reproduce", "1. Open URL\n2. Navigate to component\n3. Observe accessibility issue."),
            v.get("remediation_plan", v.get("help_url", "Refer to WCAG guidelines for fix."))
        ]
        ws_defects.append(row_data)

        # Style data row
        for col_idx in range(1, len(row_data) + 1):
            cell = ws_defects.cell(row=defect_row_idx, column=col_idx)
            cell.font = REGULAR_FONT
            cell.border = THIN_BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if col_idx == 1:
                cell.alignment = Alignment(horizontal="center", vertical="top")

        defect_row_idx += 1

    # ==========================================
    # SHEET 2: Test Case Report (Blue Header)
    # ==========================================
    ws_testcases = wb.create_sheet(title="Test Case Report")
    tc_headers = [
        "S.No", "Test Case ID", "Page URL", "Menu Name", "Component Name",
        "Feature / Element", "WCAG Criteria", "Level", "WCAG Principle",
        "Screen Reader Persona", "Expected Result", "Actual Result", "Description", "Status"
    ]
    ws_testcases.append(tc_headers)
    for col_idx in range(1, len(tc_headers) + 1):
        cell = ws_testcases.cell(row=1, column=col_idx)
        cell.fill = DARK_BLUE_FILL
        cell.font = WHITE_BOLD_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    tc_row_idx = 2
    tc_counter = 1

    # 1. Add FAIL test cases from violations
    for v in violations:
        sc_info = v.get("wcag_criteria", v.get("rule_id", "N/A"))
        sc_num = sc_info.split(" ")[0] if " " in str(sc_info) else str(sc_info)
        principle = build_wcag_principle(sc_num)

        row_data = [
            tc_counter,
            f"TC-{tc_counter:03d}",
            v.get("page_url", v.get("url", "N/A")),
            v.get("menu_name", "Navigation Menu"),
            v.get("component_name", "Interactive Component"),
            v.get("target_selector", "DOM Node"),
            v.get("wcag_criteria", "1.1.1 Non-text Content"),
            v.get("wcag_level", "A"),
            principle,
            "NVDA / JAWS User Perspective",
            v.get("expected_result", "Screen reader announces element name, role, and state correctly."),
            v.get("actual_result", v.get("help", "Screen reader fails to announce component metadata.")),
            v.get("description", "Accessibility test for screen reader compatibility."),
            "FAIL"
        ]
        ws_testcases.append(row_data)

        for col_idx in range(1, len(row_data) + 1):
            cell = ws_testcases.cell(row=tc_row_idx, column=col_idx)
            cell.font = REGULAR_FONT
            cell.border = THIN_BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if col_idx == 1:
                cell.alignment = Alignment(horizontal="center", vertical="top")
            if col_idx == 14: # Status
                cell.fill = FAIL_FILL
                cell.font = FAIL_FONT
                cell.alignment = Alignment(horizontal="center", vertical="top")

        tc_counter += 1
        tc_row_idx += 1

    # 2. Add PASS test cases
    for p in passes:
        sc_num = p.get("wcag_criteria", "1.1.1").split(" ")[0]
        principle = build_wcag_principle(sc_num)

        row_data = [
            tc_counter,
            f"TC-{tc_counter:03d}",
            p.get("page_url", "N/A"),
            "Navigation Menu",
            p.get("component", "Standard Element"),
            p.get("id", "Pass Node"),
            p.get("wcag_criteria", "1.1.1 Non-text Content"),
            "A",
            principle,
            "NVDA / JAWS User Perspective",
            "Screen reader announces accessible name and role properly.",
            "Passed automated and screen reader accessibility checks.",
            p.get("description", "Element complies with accessibility standards."),
            "PASS"
        ]
        ws_testcases.append(row_data)

        for col_idx in range(1, len(row_data) + 1):
            cell = ws_testcases.cell(row=tc_row_idx, column=col_idx)
            cell.font = REGULAR_FONT
            cell.border = THIN_BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if col_idx == 1:
                cell.alignment = Alignment(horizontal="center", vertical="top")
            if col_idx == 14: # Status
                cell.fill = PASS_FILL
                cell.font = PASS_FONT
                cell.alignment = Alignment(horizontal="center", vertical="top")

        tc_counter += 1
        tc_row_idx += 1

    # ==========================================
    # SHEET 3: WCAG Criteria Reference (Light Blue Header)
    # ==========================================
    ws_wcag = wb.create_sheet(title="WCAG Criteria Reference")
    wcag_headers = [
        "S.No", "WCAG SC #", "Criterion Title", "Level", "Principle", "Guideline", "Description", "URL"
    ]
    ws_wcag.append(wcag_headers)
    for col_idx in range(1, len(wcag_headers) + 1):
        cell = ws_wcag.cell(row=1, column=col_idx)
        cell.fill = LIGHT_BLUE_FILL
        cell.font = WHITE_BOLD_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    wcag_row_idx = 2
    wcag_items = sorted(WCAG_CRITERIA_MAP.items(), key=lambda x: x[0])
    
    for idx, (sc_code, details) in enumerate(wcag_items, start=1):
        principle = build_wcag_principle(sc_code)
        row_data = [
            idx,
            sc_code,
            details.get("title", f"Criterion {sc_code}"),
            details.get("level", "A"),
            principle,
            details.get("guideline", "WCAG 2.2"),
            details.get("description", "WCAG 2.2 Success Criterion"),
            details.get("url", f"https://www.w3.org/WAI/WCAG22/Understanding/{details.get('slug', sc_code)}")
        ]
        ws_wcag.append(row_data)

        for col_idx in range(1, len(row_data) + 1):
            cell = ws_wcag.cell(row=wcag_row_idx, column=col_idx)
            cell.font = REGULAR_FONT
            cell.border = THIN_BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if col_idx in [1, 2, 4]:
                cell.alignment = Alignment(horizontal="center", vertical="top")

        wcag_row_idx += 1

    # Remove default worksheet
    if "Sheet" in wb.sheetnames:
        wb.remove(wb["Sheet"])

    # Auto-adjust column widths
    for sheet in wb.worksheets:
        sheet.row_dimensions[1].height = 28
        for col in sheet.columns:
            col_letter = get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = 22

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
