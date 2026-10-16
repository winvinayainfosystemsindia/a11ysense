"""
Excel Report Generator for A11ySense AI.
Generates an executive 4-sheet workbook:
1. Summary (Executive Dashboard, KPI Cards, Principle & Severity Breakdown, Top 10 Defect SCs, Quality Gate)
2. Test Case Report (Dark Blue #1A237E) - Exact 14 columns
3. Defects Report (Dark Red #8B0000) - Exact 16 columns with Status Data-Validation Dropdown
4. WCAG Criteria Reference (Light Blue #1565C0) - 8 columns

Ensures:
- Formula injection protection (' prepend for =, +, -, @)
- Monospace font (Consolas 9pt) for element HTML snippets
- Clickable hyperlinks for page URLs
- Header freeze panes (A2) and autofilter on all sheets
- Strict non-technical plain English
"""
import io
import logging
from datetime import datetime
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from common.constants.wcag import WCAG_CRITERIA_MAP
from common.constants.rule_catalog import principle_for
from backend.app.core.reporting.wcag22_reference import WCAG22_A_AA_CRITERIA, principle_of

logger = logging.getLogger(__name__)

# ── Color Palette ─────────────────────────────────────────────────────────────
DARK_NAVY_FILL = PatternFill(start_color="0D1B2A", end_color="0D1B2A", fill_type="solid")
DARK_BLUE_FILL = PatternFill(start_color="1A237E", end_color="1A237E", fill_type="solid")
DARK_RED_FILL = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
LIGHT_BLUE_FILL = PatternFill(start_color="1565C0", end_color="1565C0", fill_type="solid")

CARD_HEADER_FILL = PatternFill(start_color="F0F4F8", end_color="F0F4F8", fill_type="solid")
SECTION_HEADER_FILL = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

PASS_FILL = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
PASS_FONT = Font(name="Calibri", size=10, color="2E7D32", bold=True)
FAIL_FILL = PatternFill(start_color="FFEBEE", end_color="FFEBEE", fill_type="solid")
FAIL_FONT = Font(name="Calibri", size=10, color="C62828", bold=True)
NA_FILL = PatternFill(start_color="FFF3E0", end_color="FFF3E0", fill_type="solid")
NA_FONT = Font(name="Calibri", size=10, color="E65100", bold=True)
MANUAL_FILL = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")
MANUAL_FONT = Font(name="Calibri", size=10, color="1565C0", bold=True)

SEV_CRITICAL_FILL = PatternFill(start_color="FFCDD2", end_color="FFCDD2", fill_type="solid")
SEV_CRITICAL_FONT = Font(name="Calibri", size=10, color="B71C1C", bold=True)
SEV_SERIOUS_FILL = PatternFill(start_color="FFE0B2", end_color="FFE0B2", fill_type="solid")
SEV_SERIOUS_FONT = Font(name="Calibri", size=10, color="E65100", bold=True)
SEV_MODERATE_FILL = PatternFill(start_color="FFF9C4", end_color="FFF9C4", fill_type="solid")
SEV_MODERATE_FONT = Font(name="Calibri", size=10, color="F57F17", bold=True)
SEV_MINOR_FILL = PatternFill(start_color="F1F8E9", end_color="F1F8E9", fill_type="solid")
SEV_MINOR_FONT = Font(name="Calibri", size=10, color="33691E", bold=True)

# ── Fonts ──────────────────────────────────────────────────────────────────────
TITLE_FONT = Font(name="Calibri", size=16, bold=True, color="1A237E")
SUBTITLE_FONT = Font(name="Calibri", size=11, color="555555")
SECTION_FONT = Font(name="Calibri", size=12, bold=True, color="1A237E")
CARD_TITLE_FONT = Font(name="Calibri", size=10, color="555555", bold=True)
CARD_VALUE_FONT = Font(name="Calibri", size=18, bold=True, color="1A237E")
WHITE_BOLD_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
REGULAR_FONT = Font(name="Calibri", size=10)
BOLD_FONT = Font(name="Calibri", size=10, bold=True)
CODE_FONT = Font(name="Consolas", size=9)
LINK_FONT = Font(name="Calibri", size=10, color="0563C1", underline="single")

THIN_BORDER = Border(
    left=Side(style="thin", color="D1D5DB"),
    right=Side(style="thin", color="D1D5DB"),
    top=Side(style="thin", color="D1D5DB"),
    bottom=Side(style="thin", color="D1D5DB"),
)
BOTTOM_THICK_BORDER = Border(
    left=Side(style="thin", color="D1D5DB"),
    right=Side(style="thin", color="D1D5DB"),
    top=Side(style="thin", color="D1D5DB"),
    bottom=Side(style="medium", color="1A237E"),
)

# ── Column Widths ─────────────────────────────────────────────────────────────
TC_COL_WIDTHS = [6, 14, 38, 26, 8, 16, 42, 45, 45, 45, 50, 14, 12, 30]
DEF_COL_WIDTHS = [6, 14, 14, 38, 26, 8, 16, 42, 45, 45, 45, 50, 14, 12, 50, 30]
WCAG_COL_WIDTHS = [8, 46, 8, 14, 18, 90]
SUMMARY_COL_WIDTHS = [28, 24, 20, 20, 24]


def _safe_val(val: Any) -> Any:
    """Escapes formula injection characters (=, +, -, @)."""
    if val is None:
        return ""
    if isinstance(val, (int, float, bool)):
        return val
    s = str(val)
    if s and s[0] in ('=', '+', '-', '@'):
        return "'" + s
    return s


def _status_style(status_val: str):
    s = str(status_val or "").strip().upper()
    if s == "FAIL":
        return FAIL_FILL, FAIL_FONT
    elif s == "PASS":
        return PASS_FILL, PASS_FONT
    elif s in ("NOT_APPLICABLE", "N/A"):
        return NA_FILL, NA_FONT
    elif s == "MANUAL_REVIEW":
        return MANUAL_FILL, MANUAL_FONT
    return None, REGULAR_FONT


def _severity_style(sev_val: str):
    s = str(sev_val or "").strip().lower()
    if s == "critical":
        return SEV_CRITICAL_FILL, SEV_CRITICAL_FONT
    elif s in ("serious", "high"):
        return SEV_SERIOUS_FILL, SEV_SERIOUS_FONT
    elif s in ("moderate", "medium"):
        return SEV_MODERATE_FILL, SEV_MODERATE_FONT
    elif s in ("minor", "low"):
        return SEV_MINOR_FILL, SEV_MINOR_FONT
    return None, REGULAR_FONT


def _apply_header_style(ws, num_cols: int, fill: PatternFill):
    ws.row_dimensions[1].height = 30
    for col_idx in range(1, num_cols + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = fill
        cell.font = WHITE_BOLD_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN_BORDER


def _set_col_widths(ws, widths: list):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def generate_excel_report(audit_data: Dict[str, Any]) -> bytes:
    """
    Generates a professional 4-sheet accessibility audit report:
    1. Summary
    2. Test Case Report
    3. Defects Report
    4. WCAG Criteria Reference
    """
    wb = openpyxl.Workbook()

    testcases = audit_data.get("testcases") or []
    violations = audit_data.get("violations") or []
    passes = audit_data.get("passes") or []

    # If testcases list wasn't provided, reconstruct from violations & passes
    if not testcases:
        tc_cnt = 0
        def_cnt = 0
        for v in violations:
            tc_cnt += 1
            def_cnt += 1
            testcases.append({
                "testcase_id": f"TC-{tc_cnt:04d}",
                "defect_id": f"DEF-{def_cnt:04d}",
                "rule_id": v.get("rule_id", ""),
                "testcase_name": v.get("testcase_name", v.get("help", "Defect")),
                "description": v.get("description", ""),
                "criteria": v.get("wcag_criteria", "N/A"),
                "level": v.get("wcag_level", "A"),
                "principle": v.get("wcag_principle", "N/A"),
                "severity": v.get("impact", v.get("severity", "Serious")),
                "expected_result": v.get("expected_result", ""),
                "actual_result": v.get("actual_result", ""),
                "steps_to_reproduce": v.get("steps_to_reproduce", ""),
                "remediation": v.get("remediation_plan", ""),
                "business_impact": v.get("business_impact", ""),
                "html_snippet": v.get("html_snippet", ""),
                "status": "FAIL",
                "page_url": v.get("page_url", audit_data.get("url", "")),
                "page_title": v.get("page_title", "Page"),
                "remarks": v.get("remarks", "")
            })
        for p in passes:
            tc_cnt += 1
            testcases.append({
                "testcase_id": f"TC-{tc_cnt:04d}",
                "defect_id": "N/A",
                "rule_id": p.get("rule_id", ""),
                "testcase_name": p.get("testcase_name", "Pass"),
                "description": p.get("description", ""),
                "criteria": p.get("criteria", "N/A"),
                "level": p.get("level", "A"),
                "principle": p.get("principle", "N/A"),
                "severity": "N/A",
                "expected_result": p.get("expected_result", ""),
                "actual_result": p.get("actual_result", ""),
                "steps_to_reproduce": p.get("steps_to_reproduce", ""),
                "remediation": p.get("remediation", ""),
                "business_impact": p.get("business_impact", ""),
                "html_snippet": p.get("html_snippet", ""),
                "status": "PASS",
                "page_url": p.get("page_url", audit_data.get("url", "")),
                "page_title": p.get("page_title", "Page"),
                "remarks": ""
            })

    fail_testcases = [tc for tc in testcases if tc.get("status") == "FAIL"]
    pass_testcases = [tc for tc in testcases if tc.get("status") == "PASS"]
    na_testcases = [tc for tc in testcases if tc.get("status") == "NOT_APPLICABLE"]
    manual_testcases = [tc for tc in testcases if tc.get("status") == "MANUAL_REVIEW"]

    # =========================================================================
    # SHEET 1: Summary
    # =========================================================================
    ws_sum = wb.active
    ws_sum.title = "Summary"
    _set_col_widths(ws_sum, SUMMARY_COL_WIDTHS)
    ws_sum.views.sheetView[0].showGridLines = True

    # Title Block
    ws_sum.merge_cells("A1:E1")
    t_cell = ws_sum["A1"]
    t_cell.value = "A11ySense AI — Accessibility Audit Report"
    t_cell.font = TITLE_FONT
    ws_sum.row_dimensions[1].height = 28

    ws_sum.merge_cells("A2:E2")
    sub_cell = ws_sum["A2"]
    audit_date = audit_data.get("timestamp") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    sub_cell.value = f"Audit Date: {audit_date} | Automated & Manual WCAG 2.2 Evaluation"
    sub_cell.font = SUBTITLE_FONT
    ws_sum.row_dimensions[2].height = 20

    # Key Information Table
    row_idx = 4
    ws_sum.cell(row=row_idx, column=1, value="Audit Target:").font = BOLD_FONT
    raw_target_url = audit_data.get("url") or ""
    target_url = str(raw_target_url) if raw_target_url else ""
    target_cell = ws_sum.cell(row=row_idx, column=2, value=_safe_val(target_url))
    if isinstance(target_url, str) and target_url.startswith("http"):
        target_cell.hyperlink = target_url
        target_cell.font = LINK_FONT

    pages_scanned = audit_data.get("pages_scanned") or [target_url]
    ws_sum.cell(row=row_idx + 1, column=1, value="Pages Audited:").font = BOLD_FONT
    ws_sum.cell(row=row_idx + 1, column=2, value=len(pages_scanned)).font = REGULAR_FONT

    ws_sum.cell(row=row_idx + 2, column=1, value="Total Test Cases:").font = BOLD_FONT
    ws_sum.cell(row=row_idx + 2, column=2, value=len(testcases)).font = BOLD_FONT

    row_idx += 4

    # KPI Breakdown Cards
    ws_sum.cell(row=row_idx, column=1, value="TEST CASE STATUS OVERVIEW").font = SECTION_FONT
    row_idx += 1

    headers_kpi = ["Status", "Count", "Percentage", "Description"]
    for ci, h in enumerate(headers_kpi, start=1):
        c = ws_sum.cell(row=row_idx, column=ci, value=h)
        c.fill = SECTION_HEADER_FILL
        c.font = BOLD_FONT
        c.border = THIN_BORDER
        c.alignment = Alignment(horizontal="center" if ci in (2, 3) else "left")
    row_idx += 1

    total_count = len(testcases) or 1
    kpis = [
        ("FAIL", len(fail_testcases), "Elements with confirmed accessibility defects requiring remediation", FAIL_FILL, FAIL_FONT),
        ("PASS", len(pass_testcases), "Automated requirements verified to meet WCAG standards", PASS_FILL, PASS_FONT),
        ("NOT_APPLICABLE", len(na_testcases), "Criteria not applicable to content on audited pages", NA_FILL, NA_FONT),
        ("MANUAL_REVIEW", len(manual_testcases), "Criteria requiring human verification with assistive technology", MANUAL_FILL, MANUAL_FONT),
    ]

    for status_label, count, desc, s_fill, s_font in kpis:
        c1 = ws_sum.cell(row=row_idx, column=1, value=status_label)
        c1.fill = s_fill
        c1.font = s_font
        c1.border = THIN_BORDER
        c1.alignment = Alignment(horizontal="center")

        c2 = ws_sum.cell(row=row_idx, column=2, value=count)
        c2.font = BOLD_FONT
        c2.border = THIN_BORDER
        c2.alignment = Alignment(horizontal="center")

        pct = f"{(count / total_count) * 100:.1f}%"
        c3 = ws_sum.cell(row=row_idx, column=3, value=pct)
        c3.font = REGULAR_FONT
        c3.border = THIN_BORDER
        c3.alignment = Alignment(horizontal="center")

        c4 = ws_sum.cell(row=row_idx, column=4, value=desc)
        c4.font = REGULAR_FONT
        c4.border = THIN_BORDER
        row_idx += 1

    row_idx += 2

    # Severity & Principle Breakdown
    ws_sum.cell(row=row_idx, column=1, value="DEFECT SEVERITY BREAKDOWN").font = SECTION_FONT
    ws_sum.cell(row=row_idx, column=3, value="DEFECT PRINCIPLE BREAKDOWN").font = SECTION_FONT
    row_idx += 1

    ws_sum.cell(row=row_idx, column=1, value="Severity").fill = SECTION_HEADER_FILL
    ws_sum.cell(row=row_idx, column=1).font = BOLD_FONT
    ws_sum.cell(row=row_idx, column=1).border = THIN_BORDER

    ws_sum.cell(row=row_idx, column=2, value="Defects").fill = SECTION_HEADER_FILL
    ws_sum.cell(row=row_idx, column=2).font = BOLD_FONT
    ws_sum.cell(row=row_idx, column=2).border = THIN_BORDER
    ws_sum.cell(row=row_idx, column=2).alignment = Alignment(horizontal="center")

    ws_sum.cell(row=row_idx, column=3, value="WCAG Principle").fill = SECTION_HEADER_FILL
    ws_sum.cell(row=row_idx, column=3).font = BOLD_FONT
    ws_sum.cell(row=row_idx, column=3).border = THIN_BORDER

    ws_sum.cell(row=row_idx, column=4, value="Defects").fill = SECTION_HEADER_FILL
    ws_sum.cell(row=row_idx, column=4).font = BOLD_FONT
    ws_sum.cell(row=row_idx, column=4).border = THIN_BORDER
    ws_sum.cell(row=row_idx, column=4).alignment = Alignment(horizontal="center")
    row_idx += 1

    sev_counts = {
        "Critical": sum(1 for tc in fail_testcases if str(tc.get("severity", "")).lower() == "critical"),
        "Serious": sum(1 for tc in fail_testcases if str(tc.get("severity", "")).lower() in ("serious", "high")),
        "Moderate": sum(1 for tc in fail_testcases if str(tc.get("severity", "")).lower() in ("moderate", "medium")),
        "Minor": sum(1 for tc in fail_testcases if str(tc.get("severity", "")).lower() in ("minor", "low")),
    }

    prin_counts = {
        "Perceivable": sum(1 for tc in fail_testcases if "perceivable" in str(tc.get("principle", "")).lower()),
        "Operable": sum(1 for tc in fail_testcases if "operable" in str(tc.get("principle", "")).lower()),
        "Understandable": sum(1 for tc in fail_testcases if "understandable" in str(tc.get("principle", "")).lower()),
        "Robust": sum(1 for tc in fail_testcases if "robust" in str(tc.get("principle", "")).lower()),
    }

    sev_list = list(sev_counts.items())
    prin_list = list(prin_counts.items())

    for idx in range(4):
        s_name, s_cnt = sev_list[idx]
        p_name, p_cnt = prin_list[idx]

        scell1 = ws_sum.cell(row=row_idx, column=1, value=s_name)
        s_fill, s_font = _severity_style(s_name)
        if s_fill:
            scell1.fill = s_fill
        scell1.font = s_font
        scell1.border = THIN_BORDER

        scell2 = ws_sum.cell(row=row_idx, column=2, value=s_cnt)
        scell2.font = BOLD_FONT
        scell2.border = THIN_BORDER
        scell2.alignment = Alignment(horizontal="center")

        pcell1 = ws_sum.cell(row=row_idx, column=3, value=p_name)
        pcell1.font = REGULAR_FONT
        pcell1.border = THIN_BORDER

        pcell2 = ws_sum.cell(row=row_idx, column=4, value=p_cnt)
        pcell2.font = BOLD_FONT
        pcell2.border = THIN_BORDER
        pcell2.alignment = Alignment(horizontal="center")

        row_idx += 1

    row_idx += 2

    # Top Failed Criteria Table
    ws_sum.cell(row=row_idx, column=1, value="TOP FAILED WCAG CRITERIA").font = SECTION_FONT
    row_idx += 1

    sc_fail_counts: Dict[str, int] = {}
    sc_meta_map: Dict[str, Dict[str, str]] = {}
    for tc in fail_testcases:
        crit = tc.get("criteria", "N/A")
        sc_fail_counts[crit] = sc_fail_counts.get(crit, 0) + 1
        if crit not in sc_meta_map:
            sc_meta_map[crit] = {
                "level": tc.get("level", "A"),
                "principle": tc.get("principle", "N/A")
            }

    top_criteria = sorted(sc_fail_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    top_headers = ["Rank", "WCAG Criteria", "Level", "Principle", "Defects Found"]
    for ci, h in enumerate(top_headers, start=1):
        c = ws_sum.cell(row=row_idx, column=ci, value=h)
        c.fill = SECTION_HEADER_FILL
        c.font = BOLD_FONT
        c.border = THIN_BORDER
        c.alignment = Alignment(horizontal="center" if ci in (1, 3, 4, 5) else "left")
    row_idx += 1

    if top_criteria:
        for rank, (crit, cnt) in enumerate(top_criteria, start=1):
            meta = sc_meta_map.get(crit, {})
            c1 = ws_sum.cell(row=row_idx, column=1, value=rank)
            c1.alignment = Alignment(horizontal="center")
            c1.border = THIN_BORDER

            c2 = ws_sum.cell(row=row_idx, column=2, value=_safe_val(crit))
            c2.font = BOLD_FONT
            c2.border = THIN_BORDER

            c3 = ws_sum.cell(row=row_idx, column=3, value=meta.get("level", "A"))
            c3.alignment = Alignment(horizontal="center")
            c3.border = THIN_BORDER

            c4 = ws_sum.cell(row=row_idx, column=4, value=meta.get("principle", "N/A"))
            c4.alignment = Alignment(horizontal="center")
            c4.border = THIN_BORDER

            c5 = ws_sum.cell(row=row_idx, column=5, value=cnt)
            c5.alignment = Alignment(horizontal="center")
            c5.font = BOLD_FONT
            c5.border = THIN_BORDER
            row_idx += 1
    else:
        ws_sum.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=5)
        empty_c = ws_sum.cell(row=row_idx, column=1, value="No accessibility violations detected.")
        empty_c.font = Font(name="Calibri", size=10, italic=True, color="2E7D32")
        empty_c.border = THIN_BORDER
        row_idx += 1

    row_idx += 2

    # Quality Gate Summary
    ws_sum.cell(row=row_idx, column=1, value="QUALITY GATE EVALUATION").font = SECTION_FONT
    row_idx += 1

    crit_ser_count = sev_counts["Critical"] + sev_counts["Serious"]
    qg_status = "PASSED" if crit_ser_count == 0 and len(fail_testcases) == 0 else (
        "WARNING" if crit_ser_count == 0 else "ACTION REQUIRED"
    )
    qg_fill = PASS_FILL if qg_status == "PASSED" else (NA_FILL if qg_status == "WARNING" else FAIL_FILL)
    qg_font = PASS_FONT if qg_status == "PASSED" else (NA_FONT if qg_status == "WARNING" else FAIL_FONT)

    ws_sum.cell(row=row_idx, column=1, value="Quality Gate Status:").font = BOLD_FONT
    qgc = ws_sum.cell(row=row_idx, column=2, value=qg_status)
    qgc.fill = qg_fill
    qgc.font = qg_font
    qgc.alignment = Alignment(horizontal="center")
    qgc.border = THIN_BORDER

    ws_sum.merge_cells(start_row=row_idx, start_column=3, end_row=row_idx, end_column=5)
    qg_msg = f"{crit_ser_count} Critical/Serious barriers identified." if crit_ser_count > 0 else "No high-impact barriers found."
    ws_sum.cell(row=row_idx, column=3, value=qg_msg).font = REGULAR_FONT

    # AI / LLM Cost Breakdown (Claude Sonnet vs Gemini)
    llm_usage_data = audit_data.get("llm_usage") or {}
    by_provider = llm_usage_data.get("by_provider") or {}
    if by_provider:
        row_idx += 3
        ws_sum.cell(row=row_idx, column=1, value="AI & LLM AUDIT COST SUMMARY").font = SECTION_FONT
        row_idx += 1

        cost_headers = ["Provider / Model", "API Calls", "Input Tokens", "Output Tokens", "Cost (USD)"]
        for ci, h in enumerate(cost_headers, start=1):
            c = ws_sum.cell(row=row_idx, column=ci, value=h)
            c.fill = SECTION_HEADER_FILL
            c.font = BOLD_FONT
            c.border = THIN_BORDER
            c.alignment = Alignment(horizontal="center" if ci in (2, 3, 4, 5) else "left")
        row_idx += 1

        total_cost = 0.0
        for prov_key, pdata in by_provider.items():
            label = pdata.get("label") or prov_key.capitalize()
            calls = pdata.get("calls", 0)
            in_tok = pdata.get("input_tokens", 0)
            out_tok = pdata.get("output_tokens", 0)
            cost_val = pdata.get("cost_usd", 0.0)
            total_cost += cost_val

            c1 = ws_sum.cell(row=row_idx, column=1, value=label)
            c1.font = BOLD_FONT
            c1.border = THIN_BORDER

            c2 = ws_sum.cell(row=row_idx, column=2, value=calls)
            c2.alignment = Alignment(horizontal="center")
            c2.border = THIN_BORDER

            c3 = ws_sum.cell(row=row_idx, column=3, value=f"{in_tok:,}")
            c3.alignment = Alignment(horizontal="center")
            c3.border = THIN_BORDER

            c4 = ws_sum.cell(row=row_idx, column=4, value=f"{out_tok:,}")
            c4.alignment = Alignment(horizontal="center")
            c4.border = THIN_BORDER

            c5 = ws_sum.cell(row=row_idx, column=5, value=f"${cost_val:.4f}")
            c5.font = BOLD_FONT
            c5.alignment = Alignment(horizontal="center")
            c5.border = THIN_BORDER
            row_idx += 1

        # Total cost row
        c1 = ws_sum.cell(row=row_idx, column=1, value="Total AI Audit Cost")
        c1.font = BOLD_FONT
        c1.fill = CARD_HEADER_FILL
        c1.border = THIN_BORDER

        ws_sum.merge_cells(start_row=row_idx, start_column=2, end_row=row_idx, end_column=4)
        for col in range(2, 5):
            ws_sum.cell(row=row_idx, column=col).border = THIN_BORDER
            ws_sum.cell(row=row_idx, column=col).fill = CARD_HEADER_FILL

        c5 = ws_sum.cell(row=row_idx, column=5, value=f"${total_cost:.4f}")
        c5.font = BOLD_FONT
        c5.fill = CARD_HEADER_FILL
        c5.alignment = Alignment(horizontal="center")
        c5.border = THIN_BORDER
        row_idx += 1

        # Operational Purpose Breakdown (Defects, Testcases, Other)
        by_category = llm_usage_data.get("by_category") or {}
        if by_category:
            row_idx += 2
            ws_sum.cell(row=row_idx, column=1, value="AI USAGE BY AUDIT OPERATION").font = SECTION_FONT
            row_idx += 1

            cat_headers = ["Audit Operation", "API Calls", "Input Tokens", "Output Tokens", "Cost (USD)"]
            for ci, h in enumerate(cat_headers, start=1):
                c = ws_sum.cell(row=row_idx, column=ci, value=h)
                c.fill = SECTION_HEADER_FILL
                c.font = BOLD_FONT
                c.border = THIN_BORDER
                c.alignment = Alignment(horizontal="center" if ci in (2, 3, 4, 5) else "left")
            row_idx += 1

            for cat_key in ["defect", "testcase", "other"]:
                cdata = by_category.get(cat_key)
                if not cdata:
                    continue
                label = cdata.get("label") or cat_key.capitalize()
                calls = cdata.get("calls", 0)
                in_tok = cdata.get("input_tokens", 0)
                out_tok = cdata.get("output_tokens", 0)
                cost_val = cdata.get("cost_usd", 0.0)

                c1 = ws_sum.cell(row=row_idx, column=1, value=label)
                c1.font = BOLD_FONT
                c1.border = THIN_BORDER

                c2 = ws_sum.cell(row=row_idx, column=2, value=calls)
                c2.alignment = Alignment(horizontal="center")
                c2.border = THIN_BORDER

                c3 = ws_sum.cell(row=row_idx, column=3, value=f"{in_tok:,}")
                c3.alignment = Alignment(horizontal="center")
                c3.border = THIN_BORDER

                c4 = ws_sum.cell(row=row_idx, column=4, value=f"{out_tok:,}")
                c4.alignment = Alignment(horizontal="center")
                c4.border = THIN_BORDER

                c5 = ws_sum.cell(row=row_idx, column=5, value=f"${cost_val:.4f}")
                c5.font = BOLD_FONT
                c5.alignment = Alignment(horizontal="center")
                c5.border = THIN_BORDER
                row_idx += 1

    # =========================================================================
    # OPTIONAL SHEET: Regression Summary (if regression data present)
    # =========================================================================
    regression_info = audit_data.get("regression")
    if regression_info:
        ws_reg = wb.create_sheet(title="Regression Summary")
        ws_reg.views.sheetView[0].showGridLines = True
        ws_reg.freeze_panes = "A2"
        _set_col_widths(ws_reg, [18, 16, 26, 35, 14, 14, 30])

        run_num = regression_info.get("run_number", 1)
        prev_num = regression_info.get("previous_run_number")
        score = regression_info.get("score", 100.0)
        prev_score = regression_info.get("previous_score", 100.0)
        score_delta = regression_info.get("score_delta", 0.0)
        delta_str = f"+{score_delta}" if score_delta > 0 else f"{score_delta}"

        # Title
        ws_reg.merge_cells("A1:E1")
        r_title = ws_reg["A1"]
        r_title.value = f"A11ySense AI — Regression Summary (Run #{run_num} vs Run #{prev_num or 'Baseline'})"
        r_title.font = TITLE_FONT
        ws_reg.row_dimensions[1].height = 26

        # Score comparison
        ws_reg.cell(row=3, column=1, value="Current Score:").font = BOLD_FONT
        sc_c = ws_reg.cell(row=3, column=2, value=score)
        sc_c.font = CARD_VALUE_FONT
        ws_reg.cell(row=3, column=3, value=f"Previous: {prev_score} (Delta: {delta_str})").font = REGULAR_FONT

        # Table of counts
        headers = ["Fixed Defects", "New Defects", "Reopened", "Still Open", "Not Retested"]
        vals = [
            regression_info.get("defects_fixed", 0),
            regression_info.get("defects_new", 0),
            regression_info.get("defects_reopened", 0),
            regression_info.get("defects_open", 0),
            regression_info.get("defects_not_retested", 0),
        ]
        ws_reg.row_dimensions[5].height = 22
        for ci, (h, val) in enumerate(zip(headers, vals), start=1):
            hc = ws_reg.cell(row=5, column=ci, value=h)
            hc.fill = SECTION_HEADER_FILL
            hc.font = BOLD_FONT
            hc.alignment = Alignment(horizontal="center")
            hc.border = THIN_BORDER

            vc = ws_reg.cell(row=6, column=ci, value=val)
            vc.font = BOLD_FONT
            vc.alignment = Alignment(horizontal="center")
            vc.border = THIN_BORDER
            if h == "Fixed Defects":
                vc.fill = PASS_FILL
                vc.font = PASS_FONT
            elif h in ("New Defects", "Reopened"):
                vc.fill = FAIL_FILL
                vc.font = FAIL_FONT

        dynamic_groups = regression_info.get("dynamic_groups_matched", 0)
        ws_reg.cell(row=8, column=1, value=f"Dynamic-content groups matched: {dynamic_groups}").font = BOLD_FONT

    # =========================================================================
    # SHEET 2: Test Case Report (Dark Blue Header)
    # Exact 14 columns
    # =========================================================================
    ws_tc = wb.create_sheet(title="Test Case Report")
    ws_tc.views.sheetView[0].showGridLines = True
    ws_tc.freeze_panes = "A2"

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

    for idx, tc in enumerate(testcases, start=1):
        row_num = idx + 1
        status_val = tc.get("status", "FAIL")
        sev_val = tc.get("severity", "N/A")
        page_url = tc.get("page_url", "")
        snippet = tc.get("html_snippet", "")

        row_data = [
            idx,
            _safe_val(tc.get("testcase_id", f"TC-{idx:04d}")),
            _safe_val(page_url),
            _safe_val(tc.get("criteria", "N/A")),
            _safe_val(tc.get("level", "A")),
            _safe_val(tc.get("principle", "N/A")),
            _safe_val(snippet),
            _safe_val(tc.get("description", "")),
            _safe_val(tc.get("expected_result", "")),
            _safe_val(tc.get("actual_result", "")),
            _safe_val(tc.get("steps_to_reproduce", "")),
            status_val,
            sev_val,
            _safe_val(tc.get("remarks", "")),
        ]
        ws_tc.append(row_data)

        # Apply cell styling
        for col_idx in range(1, len(tc_headers) + 1):
            cell = ws_tc.cell(row=row_num, column=col_idx)
            cell.border = THIN_BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)

            if col_idx in (1, 2, 5, 6, 12, 13):
                cell.alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)

            if col_idx == 3 and page_url.startswith("http"):
                cell.hyperlink = page_url
                cell.font = LINK_FONT
            elif col_idx == 7 and snippet and snippet != "N/A":
                cell.font = CODE_FONT
            elif col_idx == 12:
                s_fill, s_font = _status_style(status_val)
                if s_fill:
                    cell.fill = s_fill
                cell.font = s_font
            elif col_idx == 13:
                sev_fill, sev_font = _severity_style(sev_val)
                if sev_fill:
                    cell.fill = sev_fill
                cell.font = sev_font

    _set_col_widths(ws_tc, TC_COL_WIDTHS)
    ws_tc.auto_filter.ref = ws_tc.dimensions

    # =========================================================================
    # SHEET 3: Defects Report (Dark Red Header)
    # Exact 16 columns (or 21 with regression metadata)
    # =========================================================================
    ws_def = wb.create_sheet(title="Defects Report")
    ws_def.views.sheetView[0].showGridLines = True
    ws_def.freeze_panes = "A2"

    has_reg = bool(audit_data.get("regression"))
    if has_reg:
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
            "First Seen (Run)",
            "Last Seen (Run)",
            "Fixed In (Run)",
            "Reopen Count",
            "Age (days)",
            "Remarks",
        ]
        def_widths = [6, 14, 14, 38, 26, 8, 16, 42, 45, 45, 45, 50, 14, 12, 50, 14, 14, 14, 14, 12, 30]
    else:
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
        def_widths = DEF_COL_WIDTHS

    ws_def.append(def_headers)
    _apply_header_style(ws_def, len(def_headers), DARK_RED_FILL)

    for idx, tc in enumerate(fail_testcases, start=1):
        row_num = idx + 1
        page_url = tc.get("page_url", "")
        snippet = tc.get("html_snippet", "")
        sev_val = tc.get("severity", "Serious")

        # Fix suggestion / remediation
        fix_suggestion = tc.get("remediation") or ""
        if not fix_suggestion and tc.get("fix_steps"):
            fix_suggestion = "\n".join(f"{si+1}. {st}" for si, st in enumerate(tc["fix_steps"]))

        st_val = tc.get("defect_status") or "Open"
        first_seen = tc.get("first_seen_run") or 1
        last_seen = tc.get("last_seen_run") or 1
        fixed_in = tc.get("fixed_in_run") or "-"
        reopen_cnt = tc.get("reopen_count", 0)
        age_d = tc.get("age_days", 0)

        if has_reg:
            row_data = [
                idx,
                _safe_val(tc.get("defect_id", f"DEF-{idx:04d}")),
                _safe_val(tc.get("testcase_id", f"TC-{idx:04d}")),
                _safe_val(page_url),
                _safe_val(tc.get("criteria", "N/A")),
                _safe_val(tc.get("level", "A")),
                _safe_val(tc.get("principle", "N/A")),
                _safe_val(snippet),
                _safe_val(tc.get("description", "")),
                _safe_val(tc.get("expected_result", "")),
                _safe_val(tc.get("actual_result", "")),
                _safe_val(tc.get("steps_to_reproduce", "")),
                st_val,
                sev_val,
                _safe_val(fix_suggestion),
                first_seen,
                last_seen,
                fixed_in,
                reopen_cnt,
                age_d,
                _safe_val(tc.get("remarks", "")),
            ]
        else:
            row_data = [
                idx,
                _safe_val(tc.get("defect_id", f"DEF-{idx:04d}")),
                _safe_val(tc.get("testcase_id", f"TC-{idx:04d}")),
                _safe_val(page_url),
                _safe_val(tc.get("criteria", "N/A")),
                _safe_val(tc.get("level", "A")),
                _safe_val(tc.get("principle", "N/A")),
                _safe_val(snippet),
                _safe_val(tc.get("description", "")),
                _safe_val(tc.get("expected_result", "")),
                _safe_val(tc.get("actual_result", "")),
                _safe_val(tc.get("steps_to_reproduce", "")),
                st_val,
                sev_val,
                _safe_val(fix_suggestion),
                _safe_val(tc.get("remarks", "")),
            ]
        ws_def.append(row_data)

        for col_idx in range(1, len(def_headers) + 1):
            cell = ws_def.cell(row=row_num, column=col_idx)
            cell.border = THIN_BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)

            if col_idx in (1, 2, 3, 6, 7, 13, 14):
                cell.alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)

            if col_idx == 4 and page_url.startswith("http"):
                cell.hyperlink = page_url
                cell.font = LINK_FONT
            elif col_idx == 8 and snippet and snippet != "N/A":
                cell.font = CODE_FONT
            elif col_idx == 13:
                cell.font = BOLD_FONT
            elif col_idx == 14:
                sev_fill, sev_font = _severity_style(sev_val)
                if sev_fill:
                    cell.fill = sev_fill
                cell.font = sev_font

    _set_col_widths(ws_def, def_widths)
    ws_def.auto_filter.ref = ws_def.dimensions

    # Add Data Validation Dropdown for Status (Open, In Progress, Resolved, Closed)
    if len(fail_testcases) > 0:
        dv = DataValidation(type="list", formula1='"Open,In Progress,Resolved,Closed"', allow_blank=True)
        dv.error = "Please choose a valid status: Open, In Progress, Resolved, Closed"
        dv.errorTitle = "Invalid Defect Status"
        dv.prompt = "Select defect remediation status"
        dv.promptTitle = "Status Selection"
        ws_def.add_data_validation(dv)
        dv.add(f"M2:M{len(fail_testcases) + 1}")

    # =========================================================================
    # SHEET 4: WCAG Criteria Reference (Light Blue Header)
    # =========================================================================
    ws_wcag = wb.create_sheet(title="WCAG Criteria Reference")
    ws_wcag.views.sheetView[0].showGridLines = True
    ws_wcag.freeze_panes = "A2"

    wcag_headers = [
        "Sl. No",
        "Criteria",
        "Level",
        "WCAG Version",
        "WCAG Principle",
        "Description",
    ]
    ws_wcag.append(wcag_headers)
    _apply_header_style(ws_wcag, len(wcag_headers), LIGHT_BLUE_FILL)

    for idx, (sc_code, title, level, version, desc) in enumerate(WCAG22_A_AA_CRITERIA, start=1):
        row_num = idx + 1
        ws_wcag.append([
            idx,
            f"{sc_code} {title}",
            level,
            version,
            principle_of(sc_code),
            desc,
        ])

        for col_idx in range(1, len(wcag_headers) + 1):
            cell = ws_wcag.cell(row=row_num, column=col_idx)
            cell.border = THIN_BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)

            if col_idx in (1, 3, 4, 5):
                cell.alignment = Alignment(horizontal="center", vertical="top")

    _set_col_widths(ws_wcag, WCAG_COL_WIDTHS)
    ws_wcag.auto_filter.ref = ws_wcag.dimensions

    # Serialize to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
