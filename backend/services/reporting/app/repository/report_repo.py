import io
import os
import json
import zipfile
import logging
from typing import Optional, List, Dict, Any

from common.config import get_audit_storage_path
from common.utils.event_bus import read_events

logger = logging.getLogger(__name__)

class ReportRepository:
    def get_screenshot_file_path(self, task_id: str, filename: str) -> Optional[str]:
        """Serves a captured defect screenshot path for the given task."""
        reports_dir = get_audit_storage_path(task_id)
        file_path = os.path.join(reports_dir, filename)
        if os.path.exists(file_path):
            return file_path
        return None

    def load_report_json(self, task_id: str) -> Optional[List[Dict[str, Any]]]:
        """Loads compiled report JSON list if it exists."""
        reports_dir = get_audit_storage_path(task_id)
        json_path = os.path.join(reports_dir, f"testcase_report_{task_id}.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def generate_excel_file(self, testcases: List[Dict[str, Any]], task_id: Optional[str] = None) -> io.BytesIO:
        """Generates a styled Excel sheet with Summary, Test Cases, and Defects tabs."""
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from common.constants.wcag import A11YSENSE_AUDIT_SCOPE, A11YSENSE_MANUAL_REVIEW_CRITERIA, WCAG_CRITERIA_MAP

        wb = openpyxl.Workbook()
        wb.remove(wb.active) # Remove default sheet
        
        font_family = "Segoe UI"
        header_font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
        data_font = Font(name=font_family, size=10)
        code_font = Font(name="Consolas", size=9)
        
        header_fill = PatternFill(start_color="2B579A", end_color="2B579A", fill_type="solid")
        zebra_fill = PatternFill(start_color="F2F6FB", end_color="F2F6FB", fill_type="solid")
        pass_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
        fail_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
        na_fill = PatternFill(start_color="E2E3E5", end_color="E2E3E5", fill_type="solid")
        manual_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
        
        border_thin = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )
        
        align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
        align_left = Alignment(horizontal='left', vertical='top', wrap_text=True)
        
        headers = [
            "S.No", "Test Case ID", "Test Case Name", "Page Title", "Page URL", 
            "Rule ID", "Criteria", "Level", "Severity", "Status", "Description", 
            "Expected Result", "Actual Result", "Steps to Reproduce", "Remediation", 
            "Refined By", "HTML Snippet", "Screenshot"
        ]
        
        def populate_sheet(ws, cases):
            ws.append(headers)
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = border_thin
                
            ws.row_dimensions[1].height = 28
            
            for row_idx, tc in enumerate(cases, 2):
                steps = tc.get("steps_to_reproduce", "N/A")
                if isinstance(steps, list):
                    steps = "\n".join(str(s) for s in steps)
                else:
                    steps = str(steps) if steps is not None else "N/A"
                    
                remediation = tc.get("remediation", "N/A")
                if isinstance(remediation, list):
                    remediation = "\n".join(str(r) for r in remediation)
                else:
                    remediation = str(remediation) if remediation is not None else "N/A"

                row_data = [
                    row_idx - 1,
                    tc.get("testcase_id", "N/A"),
                    tc.get("testcase_name", "N/A"),
                    tc.get("page_title", "N/A"),
                    tc.get("page_url", "N/A"),
                    tc.get("rule_id", "N/A"),
                    tc.get("criteria", "N/A"),
                    tc.get("level", "N/A"),
                    tc.get("severity", "N/A"),
                    tc.get("status", "N/A"),
                    tc.get("description", "N/A"),
                    tc.get("expected_result", "N/A"),
                    tc.get("actual_result", "N/A"),
                    steps,
                    remediation,
                    tc.get("refined_by", "N/A"),
                    tc.get("html_snippet", "N/A"),
                    tc.get("screenshot", "N/A")
                ]
                
                ws.append(row_data)
                ws.row_dimensions[row_idx].height = 20
                
                for col_idx, val in enumerate(row_data, 1):
                    cell = ws.cell(row=row_idx, column=col_idx)
                    cell.border = border_thin
                    
                    if col_idx in [1, 2, 7, 8, 9, 10, 18]:
                        cell.alignment = align_center
                    else:
                        cell.alignment = align_left
                        
                    if col_idx in [2, 6, 17]:
                        cell.font = code_font
                    else:
                        cell.font = data_font
                        
                    if row_idx % 2 == 1:
                        cell.fill = zebra_fill
                        
                    if col_idx == 10:
                        if val == "PASS":
                            cell.fill = pass_fill
                            cell.font = Font(name=font_family, size=10, bold=True, color="155724")
                        elif val == "FAIL":
                            cell.fill = fail_fill
                            cell.font = Font(name=font_family, size=10, bold=True, color="721C24")
                        elif val == "NOT_APPLICABLE":
                            cell.fill = na_fill
                            cell.font = Font(name=font_family, size=10, bold=True, color="383D41")
                        elif val == "MANUAL_REVIEW":
                            cell.fill = manual_fill
                            cell.font = Font(name=font_family, size=10, bold=True, color="856404")
                            
                    if col_idx == 9:
                        sev = str(val).lower()
                        if sev in ["critical", "blocker"]:
                            cell.font = Font(name=font_family, size=10, bold=True, color="721C24")
                        elif sev in ["serious", "high"]:
                            cell.font = Font(name=font_family, size=10, bold=True, color="856404")
                            
            ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(cases) + 1}"
            
            for col in ws.columns:
                max_len = 0
                for cell in col:
                    val_str = str(cell.value or '')
                    lines = val_str.split('\n')
                    longest_line = max(len(l) for l in lines) if lines else 0
                    if longest_line > max_len:
                        max_len = longest_line
                col_letter = get_column_letter(col[0].column)
                adjusted_width = min(max(max_len + 4, 12), 40)
                ws.column_dimensions[col_letter].width = adjusted_width

        # ── Build criteria status from testcases ──────────────────────────────
        criteria_status = {}  # code -> {"level": ..., "status": "PASS"|"FAIL"|"NOT_APPLICABLE"|"MANUAL_REVIEW"}
        for tc in testcases:
            crit = tc.get("criteria", "N/A")
            level = tc.get("level", "N/A")
            status = tc.get("status", "N/A")
            if crit != "N/A":
                code = crit.split(" ")[0]
                if code not in criteria_status:
                    criteria_status[code] = {"level": level, "status": status}
                # FAIL overrides everything, PASS overrides NOT_APPLICABLE
                if status == "FAIL":
                    criteria_status[code]["status"] = "FAIL"
                elif status == "PASS" and criteria_status[code]["status"] not in ("FAIL",):
                    criteria_status[code]["status"] = "PASS"

        # ── Load summary metadata ────────────────────────────────────────────
        wcag_stats = None
        url_scanned = "N/A"
        acc_score = "N/A"
        total_violations = 0

        if task_id:
            try:
                reports_dir = get_audit_storage_path(task_id)
                summary_path = os.path.join(reports_dir, f"summary_{task_id}.json")
                if os.path.exists(summary_path):
                    with open(summary_path, "r", encoding="utf-8") as f:
                        sum_data = json.load(f)
                        wcag_stats = sum_data.get("wcag_stats")
                        acc_score = sum_data.get("accessibility_score", "N/A")
                        total_violations = sum_data.get("total_violations", 0)
                if testcases:
                    url_scanned = testcases[0].get("page_url", "N/A")
            except Exception as e:
                logger.warning(f"Failed to load summary metadata for Excel summary sheet: {e}")

        # ── Summary Sheet ────────────────────────────────────────────────────
        ws_sum = wb.create_sheet(title="Summary")

        # Title row
        ws_sum.merge_cells("A1:E1")
        cell_title = ws_sum["A1"]
        cell_title.value = "Accessibility Compliance Audit Summary"
        cell_title.font = Font(name=font_family, size=16, bold=True, color="FFFFFF")
        cell_title.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        cell_title.alignment = align_center
        ws_sum.row_dimensions[1].height = 40

        # Meta info
        ws_sum.append([])
        ws_sum.append(["Scanned URL:", url_scanned])
        ws_sum.append(["Total Defects:", total_violations])
        ws_sum.append(["Compliance Score:", f"{acc_score}%" if isinstance(acc_score, (int, float)) else acc_score])

        for r in [3, 4, 5]:
            ws_sum.cell(row=r, column=1).font = Font(name=font_family, size=10, bold=True, color="1F4E78")
            ws_sum.cell(row=r, column=2).font = data_font
            ws_sum.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
            ws_sum.row_dimensions[r].height = 20

        # Coverage summary
        ws_sum.append([])
        ws_sum.append(["WCAG 2.1 Level A & AA — Criteria Coverage"])
        ws_sum.merge_cells("A7:E7")
        ws_sum["A7"].font = Font(name=font_family, size=12, bold=True, color="1F4E78")
        ws_sum.row_dimensions[7].height = 24

        level_a_covered = wcag_stats["level_a_covered"] if wcag_stats else "—"
        level_a_total = wcag_stats["level_a_total"] if wcag_stats else 19
        level_aa_covered = wcag_stats["level_aa_covered"] if wcag_stats else "—"
        level_aa_total = wcag_stats["level_aa_total"] if wcag_stats else 7

        ws_sum.append(["Automated Scope — Level A:", f"{level_a_covered} / {level_a_total} criteria applicable"])
        ws_sum.append(["Automated Scope — Level AA:", f"{level_aa_covered} / {level_aa_total} criteria applicable"])
        ws_sum.append(["Manual Review Required:", f"{len(A11YSENSE_MANUAL_REVIEW_CRITERIA)} criteria (not covered by automated audit)"])

        for r in [8, 9, 10]:
            ws_sum.cell(row=r, column=1).font = Font(name=font_family, size=10, bold=True)
            ws_sum.cell(row=r, column=2).font = data_font
            ws_sum.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
            ws_sum.row_dimensions[r].height = 20

        # Detailed Criteria Table
        ws_sum.append([])
        table_headers = ["WCAG Criterion", "Level", "Scope", "Status", "Description"]
        ws_sum.append(table_headers)
        header_row = 12
        ws_sum.row_dimensions[header_row].height = 24

        for col_idx, h in enumerate(table_headers, 1):
            c = ws_sum.cell(row=header_row, column=col_idx)
            c.font = header_font
            c.fill = header_fill
            c.alignment = align_center
            c.border = border_thin

        row_num = header_row + 1

        # Section 1: Automated scope (26 criteria)
        for scope_crit in A11YSENSE_AUDIT_SCOPE:
            code = scope_crit["code"]
            full_name = WCAG_CRITERIA_MAP.get(code, f"{code} {scope_crit['name']}")
            level = scope_crit["level"]

            if code in criteria_status:
                state = criteria_status[code]["status"]
                if state == "FAIL":
                    status_text = "Non-compliant"
                    desc = "Defects identified. See 'Defects' sheet for details."
                elif state == "PASS":
                    status_text = "Compliant"
                    desc = "Tested and verified compliant."
                else:
                    status_text = "Not Applicable"
                    desc = "No elements matching this criterion were found on the website."
            else:
                status_text = "Not Applicable"
                desc = "No elements matching this criterion were found on the website."

            ws_sum.append([full_name, level, "Automated", status_text, desc])
            ws_sum.row_dimensions[row_num].height = 20

            for col_idx in range(1, 6):
                c = ws_sum.cell(row=row_num, column=col_idx)
                c.border = border_thin
                c.font = data_font
                if col_idx in [2, 3, 4]:
                    c.alignment = align_center
                else:
                    c.alignment = align_left

                if col_idx == 4:
                    if status_text == "Compliant":
                        c.fill = pass_fill
                        c.font = Font(name=font_family, size=10, bold=True, color="155724")
                    elif status_text == "Non-compliant":
                        c.fill = fail_fill
                        c.font = Font(name=font_family, size=10, bold=True, color="721C24")
                    else:
                        c.fill = na_fill
                        c.font = Font(name=font_family, size=10, bold=True, color="383D41")

            row_num += 1

        # Section 2: Manual review criteria (24 criteria)
        for manual_crit in A11YSENSE_MANUAL_REVIEW_CRITERIA:
            code = manual_crit["code"]
            full_name = WCAG_CRITERIA_MAP.get(code, f"{code} {manual_crit['name']}")
            level = manual_crit["level"]
            group = manual_crit.get("group", "B")

            if group == "A":
                desc = "Can potentially be automated in a future release. Manual testing recommended."
            else:
                desc = "Requires human judgement, real device testing, or watching/listening to content."

            ws_sum.append([full_name, level, "Manual Review", "Manual Review Required", desc])
            ws_sum.row_dimensions[row_num].height = 20

            for col_idx in range(1, 6):
                c = ws_sum.cell(row=row_num, column=col_idx)
                c.border = border_thin
                c.font = data_font
                if col_idx in [2, 3, 4]:
                    c.alignment = align_center
                else:
                    c.alignment = align_left

                if col_idx == 4:
                    c.fill = manual_fill
                    c.font = Font(name=font_family, size=10, bold=True, color="856404")

            row_num += 1

        ws_sum.column_dimensions['A'].width = 40
        ws_sum.column_dimensions['B'].width = 10
        ws_sum.column_dimensions['C'].width = 18
        ws_sum.column_dimensions['D'].width = 24
        ws_sum.column_dimensions['E'].width = 55

        # ── Test Cases and Defects Sheets ─────────────────────────────────────
        ws_tc = wb.create_sheet(title="Test Cases")
        populate_sheet(ws_tc, testcases)
        
        ws_def = wb.create_sheet(title="Defects")
        defects = [tc for tc in testcases if tc.get("status") == "FAIL"]
        populate_sheet(ws_def, defects)
        
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def create_zip_archive(self, task_id: str, testcases: List[Dict[str, Any]], excel_file: io.BytesIO) -> io.BytesIO:
        """Compiles Excel, JSON, and screenshots into a single ZIP archive buffer."""
        reports_dir = get_audit_storage_path(task_id)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Add json file (formatted for readability)
            json_content = json.dumps(testcases, indent=2, ensure_ascii=False)
            zip_file.writestr("report.json", json_content.encode("utf-8"))
            
            # 2. Add excel file
            zip_file.writestr("report.xlsx", excel_file.getvalue())
            
            # 3. Add screenshots folder
            screenshots_added = set()
            for tc in testcases:
                screenshot_filename = tc.get("screenshot")
                if screenshot_filename and screenshot_filename != "N/A":
                    if screenshot_filename not in screenshots_added:
                        src_screenshot_path = os.path.join(reports_dir, screenshot_filename)
                        if os.path.exists(src_screenshot_path):
                            zip_file.write(src_screenshot_path, arcname=f"screenshots/{screenshot_filename}")
                            screenshots_added.add(screenshot_filename)
        zip_buffer.seek(0)
        return zip_buffer

    def read_analyzed_events(self, last_id: str, block_ms: int = 2000) -> list:
        """Polls the 'audit:analyzed' Redis stream for new analysis events."""
        try:
            return read_events("audit:analyzed", last_id=last_id, block_ms=block_ms) or []
        except Exception as e:
            logger.error(f"[ReportRepository] Error reading events: {e}")
            return []

report_repo = ReportRepository()
