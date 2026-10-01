"""
Excel Report Generator for A11ySense AI.
Generates an executive 3-sheet workbook:
1. Test Case Report (Dark Blue #1a237e)
2. Defects Report (Dark Red #8B0000)
3. WCAG Criteria Reference (Light Blue #1565c0)

ALL descriptive content (Description, Expected Result, Actual Result,
Steps to Reproduce, AI Fix Suggestion) comes from the LLM-generated
metadata_json field — nothing is hardcoded.
"""
import io
import logging
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from common.constants.wcag import WCAG_CRITERIA_MAP

logger = logging.getLogger(__name__)

# ── Colour palette ──────────────────────────────────────────────────────────
DARK_RED_FILL = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
DARK_BLUE_FILL = PatternFill(start_color="1A237E", end_color="1A237E", fill_type="solid")
LIGHT_BLUE_FILL = PatternFill(start_color="1565C0", end_color="1565C0", fill_type="solid")

# ── Fonts ───────────────────────────────────────────────────────────────────
WHITE_BOLD_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
REGULAR_FONT = Font(name="Calibri", size=10)
BOLD_FONT = Font(name="Calibri", size=10, bold=True)

PASS_FILL = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
PASS_FONT = Font(name="Calibri", size=10, color="2E7D32", bold=True)
FAIL_FILL = PatternFill(start_color="FFEBEE", end_color="FFEBEE", fill_type="solid")
FAIL_FONT = Font(name="Calibri", size=10, color="C62828", bold=True)
NA_FILL = PatternFill(start_color="FFF3E0", end_color="FFF3E0", fill_type="solid")
NA_FONT = Font(name="Calibri", size=10, color="E65100", bold=True)
MANUAL_FILL = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")
MANUAL_FONT = Font(name="Calibri", size=10, color="1565C0", bold=True)

THIN_BORDER = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC"),
)

# ── Column width presets (approximate chars) ────────────────────────────────
TC_COL_WIDTHS = [6, 14, 40, 24, 8, 16, 40, 45, 45, 45, 50, 12, 12, 25]
DEF_COL_WIDTHS = [6, 14, 14, 40, 24, 8, 16, 40, 45, 45, 45, 50, 12, 12, 50, 25]
WCAG_COL_WIDTHS = [6, 10, 30, 8, 16, 24, 50, 50]


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────
def _wcag_principle(sc_code: str) -> str:
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


def _extract_sc_number(sc_info: str) -> str:
    """Extract just the SC number (e.g. '1.1.1') from a string like '1.1.1 Non-text Content'."""
    parts = str(sc_info).split(" ", 1)
    return parts[0] if parts else "N/A"


def _get_meta(v: Dict[str, Any]) -> Dict[str, Any]:
    """Get the LLM-generated metadata dict from a violation record."""
    meta = v.get("metadata_json") or v.get("metadata") or {}
    if not isinstance(meta, dict):
        return {}
    return meta


def _status_style(status_value: str):
    """Return (fill, font) tuple for a given test-case status."""
    s = status_value.upper()
    if s == "FAIL":
        return FAIL_FILL, FAIL_FONT
    elif s == "PASS":
        return PASS_FILL, PASS_FONT
    elif s in ("NOT_APPLICABLE", "N/A"):
        return NA_FILL, NA_FONT
    elif s == "MANUAL_REVIEW":
        return MANUAL_FILL, MANUAL_FONT
    return None, REGULAR_FONT


def _apply_row_style(ws, row_idx: int, num_cols: int, status_col: int = None, status_value: str = None):
    """Apply standard styling to a data row."""
    for col_idx in range(1, num_cols + 1):
        cell = ws.cell(row=row_idx, column=col_idx)
        cell.font = REGULAR_FONT
        cell.border = THIN_BORDER
        cell.alignment = Alignment(vertical="top", wrap_text=True)
        if col_idx == 1:
            cell.alignment = Alignment(horizontal="center", vertical="top")
    if status_col and status_value:
        fill, font = _status_style(status_value)
        cell = ws.cell(row=row_idx, column=status_col)
        if fill:
            cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center", vertical="top")


def _apply_header_style(ws, num_cols: int, fill: PatternFill):
    """Apply header row style."""
    for col_idx in range(1, num_cols + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = fill
        cell.font = WHITE_BOLD_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _set_col_widths(ws, widths: list):
    """Set column widths for a sheet."""
    ws.row_dimensions[1].height = 30
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ────────────────────────────────────────────────────────────────────────────
# Main generator — ALL content from LLM metadata, zero hardcoded values
# ────────────────────────────────────────────────────────────────────────────
def generate_excel_report(audit_data: Dict[str, Any]) -> bytes:
    """
    Generates an Excel report (.xlsx) with 3 sheets.

    ALL descriptive columns are populated from the LLM-generated
    metadata_json stored for each violation — no content is hardcoded.
    """
    wb = openpyxl.Workbook()
    default_sheet = wb.active

    violations = audit_data.get("violations", [])
    passes = audit_data.get("passes", [])

    # ==================================================================
    # SHEET 1: Test Case Report (Blue Header)
    # Columns: S.No | Testcase ID | Page URL | WCAG Criteria | Level |
    #          WCAG Principle | Element HTML Snippet | Description |
    #          Expected Result | Actual Result | Steps to Reproduce |
    #          Status | Severity | Remarks
    # ==================================================================
    ws_tc = wb.create_sheet(title="Test Case Report")
    tc_headers = [
        "S.No",
        "Testcase ID",
        "Page URL",
        "WCAG Criteria",
        "Level",
        "WCAG Principle",
        "Element HTML Snippet",
        "Description",
        "Expected Result",
        "Actual Result",
        "Steps to Reproduce",
        "Status",
        "Severity",
        "Remarks",
    ]
    ws_tc.append(tc_headers)
    _apply_header_style(ws_tc, len(tc_headers), DARK_BLUE_FILL)

    tc_counter = 0
    tc_row = 2
    # Maps: violation index → testcase_id (for linking defects to testcases)
    violation_tc_map: Dict[int, str] = {}

    # 1a) FAIL test cases from violations ─────────────────────────────────
    for idx, v in enumerate(violations):
        tc_counter += 1
        tc_id = f"TC-{tc_counter:04d}"
        violation_tc_map[idx] = tc_id

        meta = _get_meta(v)
        tc_meta = meta.get("testcase") if isinstance(meta.get("testcase"), dict) else meta

        criteria = tc_meta.get("wcag_criteria") or meta.get("wcag_criteria", v.get("wcag_criteria", ""))
        sc_num = _extract_sc_number(criteria)
        principle = tc_meta.get("wcag_principle") or _wcag_principle(sc_num)
        level = tc_meta.get("wcag_level") or meta.get("wcag_level", v.get("wcag_level", ""))
        snippet = tc_meta.get("element_html_snippet") or meta.get("element_html_snippet", "")
        if not snippet:
            # Fallback: extract from nodes
            nodes = v.get("nodes")
            if isinstance(nodes, list) and nodes:
                first = nodes[0] if isinstance(nodes[0], dict) else {}
                snippet = first.get("html", "")

        row_data = [
            tc_counter,
            tc_id,
            v.get("page_url", v.get("url", "")),
            criteria,
            level,
            principle,
            snippet,
            tc_meta.get("description") or meta.get("description", v.get("description", "")),
            tc_meta.get("expected_result") or meta.get("expected_result", v.get("expected_result", "")),
            tc_meta.get("actual_result") or meta.get("actual_result", v.get("actual_result", "")),
            tc_meta.get("steps_to_reproduce") or meta.get("steps_to_reproduce", v.get("steps_to_reproduce", "")),
            "FAIL",
            tc_meta.get("severity") or meta.get("severity", v.get("impact", "")),
            "",  # Remarks — intentionally blank for auditor to fill
        ]
        ws_tc.append(row_data)
        _apply_row_style(ws_tc, tc_row, len(tc_headers), status_col=12, status_value="FAIL")
        tc_row += 1

    # 1b) PASS test cases ─────────────────────────────────────────────────
    for p in passes:
        tc_counter += 1
        tc_id = f"TC-{tc_counter:04d}"

        meta = _get_meta(p)
        criteria = meta.get("wcag_criteria", p.get("wcag_criteria", ""))
        sc_num = _extract_sc_number(criteria)
        principle = _wcag_principle(sc_num)

        row_data = [
            tc_counter,
            tc_id,
            p.get("page_url", ""),
            criteria,
            meta.get("wcag_level", p.get("wcag_level", "")),
            principle,
            meta.get("element_html_snippet", p.get("html_snippet", "")),
            meta.get("description", p.get("description", "")),
            meta.get("expected_result", p.get("expected_result", "")),
            meta.get("actual_result", p.get("actual_result", "")),
            meta.get("steps_to_reproduce", p.get("steps_to_reproduce", "")),
            "PASS",
            "N/A",
            "",
        ]
        ws_tc.append(row_data)
        _apply_row_style(ws_tc, tc_row, len(tc_headers), status_col=12, status_value="PASS")
        tc_row += 1

    _set_col_widths(ws_tc, TC_COL_WIDTHS)

    # ==================================================================
    # SHEET 2: Defects Report (Red Header)
    # Columns: S.No | Defect ID | Testcase ID | Page URL | WCAG Criteria |
    #          Level | WCAG Principle | Element HTML Snippet | Description |
    #          Expected Result | Actual Result | Steps to Reproduce |
    #          Status | Severity | AI Suggestion to Fix | Remarks
    # ==================================================================
    ws_def = wb.create_sheet(title="Defects Report")
    def_headers = [
        "S.No",
        "Defect ID",
        "Testcase ID",
        "Page URL",
        "WCAG Criteria",
        "Level",
        "WCAG Principle",
        "Element HTML Snippet",
        "Description",
        "Expected Result",
        "Actual Result",
        "Steps to Reproduce",
        "Status",
        "Severity",
        "AI Suggestion to Fix",
        "Remarks",
    ]
    ws_def.append(def_headers)
    _apply_header_style(ws_def, len(def_headers), DARK_RED_FILL)

    def_row = 2
    for idx, v in enumerate(violations):
        defect_id = f"DEF-{idx + 1:04d}"
        linked_tc = violation_tc_map.get(idx, "")

        meta = _get_meta(v)
        def_meta = meta.get("defect") if isinstance(meta.get("defect"), dict) else meta

        criteria = def_meta.get("wcag_criteria") or meta.get("wcag_criteria", v.get("wcag_criteria", ""))
        sc_num = _extract_sc_number(criteria)
        principle = def_meta.get("wcag_principle") or _wcag_principle(sc_num)
        level = def_meta.get("wcag_level") or meta.get("wcag_level", v.get("wcag_level", ""))
        snippet = def_meta.get("element_html_snippet") or meta.get("element_html_snippet", "")
        if not snippet:
            nodes = v.get("nodes")
            if isinstance(nodes, list) and nodes:
                first = nodes[0] if isinstance(nodes[0], dict) else {}
                snippet = first.get("html", "")

        row_data = [
            idx + 1,
            defect_id,
            linked_tc,
            v.get("page_url", v.get("url", "")),
            criteria,
            level,
            principle,
            snippet,
            def_meta.get("description") or meta.get("description", v.get("description", "")),
            def_meta.get("expected_result") or meta.get("expected_result", v.get("expected_result", "")),
            def_meta.get("actual_result") or meta.get("actual_result", v.get("actual_result", "")),
            def_meta.get("steps_to_reproduce") or meta.get("steps_to_reproduce", v.get("steps_to_reproduce", "")),
            "Open",
            def_meta.get("severity") or meta.get("severity", v.get("impact", "")),
            def_meta.get("ai_fix_suggestion") or meta.get("ai_fix_suggestion", meta.get("remediation", v.get("remediation_plan", ""))),
            "",  # Remarks — blank for auditor
        ]
        ws_def.append(row_data)
        _apply_row_style(ws_def, def_row, len(def_headers), status_col=13, status_value="FAIL")
        def_row += 1

    _set_col_widths(ws_def, DEF_COL_WIDTHS)

    # ==================================================================
    # SHEET 3: WCAG Criteria Reference (Light Blue Header)
    # ==================================================================
    ws_wcag = wb.create_sheet(title="WCAG Criteria Reference")
    wcag_headers = [
        "S.No", "WCAG SC #", "Criterion Title", "Level", "Principle",
        "Guideline", "Description", "URL",
    ]
    ws_wcag.append(wcag_headers)
    _apply_header_style(ws_wcag, len(wcag_headers), LIGHT_BLUE_FILL)

    wcag_row = 2
    wcag_items = sorted(WCAG_CRITERIA_MAP.items(), key=lambda x: x[0])

    for idx, (sc_code, details) in enumerate(wcag_items, start=1):
        principle = _wcag_principle(sc_code)
        if isinstance(details, dict):
            title = details.get("title", f"Criterion {sc_code}")
            level = details.get("level", "A")
            guideline = details.get("guideline", "WCAG 2.2")
            description = details.get("description", "WCAG 2.2 Success Criterion")
            url = details.get("url", f"https://www.w3.org/WAI/WCAG22/Understanding/{details.get('slug', sc_code)}")
        else:
            title = str(details)
            level = "A"
            guideline = f"Guideline {sc_code.rsplit('.', 1)[0]}" if "." in sc_code else "WCAG 2.2"
            description = f"WCAG 2.2 Success Criterion {title}"
            url = f"https://www.w3.org/WAI/WCAG22/Understanding/{sc_code}"

        row_data = [idx, sc_code, title, level, principle, guideline, description, url]
        ws_wcag.append(row_data)

        for col_idx in range(1, len(row_data) + 1):
            cell = ws_wcag.cell(row=wcag_row, column=col_idx)
            cell.font = REGULAR_FONT
            cell.border = THIN_BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if col_idx in [1, 2, 4]:
                cell.alignment = Alignment(horizontal="center", vertical="top")

        wcag_row += 1

    _set_col_widths(ws_wcag, WCAG_COL_WIDTHS)

    # ── Cleanup & serialise ─────────────────────────────────────────────
    if "Sheet" in wb.sheetnames:
        wb.remove(wb["Sheet"])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
