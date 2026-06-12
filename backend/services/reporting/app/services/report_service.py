import os
import html
import uuid
import logging
from typing import Optional
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, StreamingResponse

from app.services.allure_manager import AllureManager
from app.schemas.audit import AuditResult
from app.repository.report_repo import report_repo
from common.config import get_audit_storage_path

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self):
        results_dir = os.getenv("ALLURE_RESULTS_DIR", "storage/reports/allure-results")
        self.allure_manager = AllureManager(results_dir)

    async def create_audit_report(self, result: AuditResult, custom_task_id: Optional[str] = None):
        """
        Coordinates the transformation of an AuditResult into a professional Allure report.
        """
        task_id = custom_task_id or str(uuid.uuid4())
        
        audit_dir = get_audit_storage_path(task_id)
        allure_dir = os.path.join(audit_dir, "allure-results")
        os.makedirs(allure_dir, exist_ok=True)
        
        # Set dynamic results dir on allure manager
        self.allure_manager.results_dir = allure_dir
        
        task_id = self.allure_manager.generate_allure_json(result, task_id)
        return {
            "status": "success",
            "task_id": task_id,
            "message": "Industry-standard Allure report generated successfully."
        }

    def get_report_screenshot(self, task_id: str, filename: str):
        """
        Serves a captured defect screenshot for the given task.
        """
        file_path = report_repo.get_screenshot_file_path(task_id, filename)
        if file_path:
            return FileResponse(file_path, media_type="image/png")
        return JSONResponse(status_code=404, content={"detail": "Screenshot not found"})

    def get_html_report(self, task_id: str):
        """
        Directly serves a gorgeous, premium HTML render of the compiled audit reports.
        """
        testcases = report_repo.load_report_json(task_id)
        if testcases is None:
            return HTMLResponse(
                content="<h1>Report Not Found</h1><p>The report for this task ID does not exist yet.</p>",
                status_code=404
            )

        fail_cases = [tc for tc in testcases if tc.get("status") == "FAIL"]
        pass_cases = [tc for tc in testcases if tc.get("status") == "PASS"]

        html_body = f"<h1>Accessibility Compliance Report</h1>"
        html_body += f"<p><strong>Scan Task ID:</strong> {task_id}</p>"
        html_body += f"<p><strong>Summary:</strong> {len(fail_cases)} Defects Found | {len(pass_cases)} Passed Checks</p>"
        html_body += "<hr/>"

        if fail_cases:
            html_body += f"<h2>Accessibility Defects ({len(fail_cases)})</h2>"
            for idx, tc in enumerate(fail_cases, start=1):
                help_url = tc.get("help_url", "")
                html_snippet = tc.get("html_snippet", "")
                
                testcase_name = str(tc.get('testcase_name', 'N/A'))
                testcase_id = str(tc.get('testcase_id', 'N/A'))
                rule_id = str(tc.get('rule_id', 'N/A'))
                page_title = str(tc.get('page_title', 'N/A'))
                page_url = str(tc.get('page_url', 'N/A'))
                criteria = str(tc.get('criteria', 'N/A'))
                level = str(tc.get('level', 'N/A'))
                severity = str(tc.get('severity', 'N/A'))
                description = str(tc.get('description', 'N/A'))
                business_impact = str(tc.get('business_impact', 'N/A'))
                refined_by = str(tc.get('refined_by', 'N/A'))

                expected_result = tc.get('expected_result', 'N/A')
                expected_result = str(expected_result) if expected_result is not None else 'N/A'
                
                actual_result = tc.get('actual_result', 'N/A')
                actual_result = str(actual_result) if actual_result is not None else 'N/A'

                steps = tc.get('steps_to_reproduce', 'N/A')
                if isinstance(steps, list):
                    steps = "\n".join(str(s) for s in steps)
                else:
                    steps = str(steps) if steps is not None else 'N/A'

                remediation = tc.get('remediation', 'N/A')
                if isinstance(remediation, list):
                    remediation = "\n".join(str(r) for r in remediation)
                else:
                    remediation = str(remediation) if remediation is not None else 'N/A'

                html_body += f"<div style='margin-bottom: 30px; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #fff;'>"
                html_body += f"<h3>Defect {idx}: {html.escape(testcase_name)}</h3>"
                html_body += "<ul style='padding-left: 20px;'>"
                html_body += f"<li><strong>Test Case ID:</strong> <code>{html.escape(testcase_id)}</code></li>"
                html_body += f"<li><strong>Rule ID:</strong> <code>{html.escape(rule_id)}</code></li>"
                html_body += f"<li><strong>Page Title:</strong> {html.escape(page_title)}</li>"
                html_body += f"<li><strong>URL:</strong> <a href='{html.escape(page_url)}' target='_blank'>{html.escape(page_url)}</a></li>"
                html_body += f"<li><strong>Criteria:</strong> {html.escape(criteria)}</li>"
                html_body += f"<li><strong>Level:</strong> {html.escape(level)}</li>"
                html_body += f"<li><strong>Severity:</strong> <span style='font-weight: 600; color: #991b1b;'>{html.escape(severity)}</span></li>"
                html_body += f"<li><strong>Description:</strong> {html.escape(description)}</li>"
                html_body += f"<li><strong>Business Impact:</strong> {html.escape(business_impact)}</li>"
                html_body += f"<li><strong>Expected Result:</strong> {html.escape(expected_result)}</li>"
                html_body += f"<li><strong>Actual Result:</strong> {html.escape(actual_result)}</li>"
                html_body += f"<li><strong>Steps To Reproduce:</strong> {html.escape(steps)}</li>"
                html_body += f"<li><strong>Remediation:</strong> {html.escape(remediation)}</li>"
                html_body += f"<li><strong>Refined By:</strong> {html.escape(refined_by)}</li>"
                
                # Show token usage sizes
                input_tokens = tc.get("input_tokens", 0)
                output_tokens = tc.get("output_tokens", 0)
                if input_tokens > 0 or output_tokens > 0:
                    html_body += f"<li><strong>AI Token Size:</strong> Input: {input_tokens} | Output: {output_tokens}</li>"

                if help_url:
                    html_body += f"<li><strong>Help URL:</strong> <a href='{html.escape(help_url)}' target='_blank'>{html.escape(help_url)}</a></li>"
                html_body += "</ul>"
                
                if html_snippet:
                    html_body += f"<p><strong>HTML Snippet:</strong></p>"
                    html_body += f"<pre><code class='language-html'>{html.escape(html_snippet)}</code></pre>"
                
                screenshot = tc.get("screenshot")
                if screenshot and screenshot != "N/A":
                    html_body += f"<p><strong>Visual Evidence (Defect Screenshot):</strong></p>"
                    html_body += f"<div style='margin-top: 10px; margin-bottom: 20px;'><img src='/report/{task_id}/screenshot/{html.escape(screenshot)}' alt='Defect Screenshot' style='max-width: 100%; border: 1px solid #cbd5e1; border-radius: 6px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);'/></div>"
                
                html_body += "</div>"

        if pass_cases:
            html_body += f"<h2>Passed Compliance Checks ({len(pass_cases)})</h2>"
            html_body += "<table>"
            html_body += "<thead><tr><th>Test Case ID</th><th>Rule ID</th><th>Page Title</th><th>Status</th></tr></thead>"
            html_body += "<tbody>"
            for tc in pass_cases[:50]:  # limit to first 50 passed checks
                html_body += "<tr>"
                html_body += f"<td><code>{html.escape(tc.get('testcase_id', 'N/A'))}</code></td>"
                html_body += f"<td>{html.escape(tc.get('rule_id', 'N/A'))}</td>"
                html_body += f"<td>{html.escape(tc.get('page_title', 'N/A'))}</td>"
                html_body += f"<td style='background-color: #f0fdf4; color: #166534; font-weight: 600;'>PASS</td>"
                html_body += "</tr>"
            html_body += "</tbody></table>"
            if len(pass_cases) > 50:
                html_body += f"<p style='font-style: italic; color: #6b7280; margin-top: 8px;'>Showing first 50 passed checks. Refer to the JSON report for full details.</p>"

        html_page = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Accessibility Audit Report - {task_id}</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Outfit', sans-serif;
                    line-height: 1.6;
                    color: #1f2937;
                    max-width: 1000px;
                    margin: 40px auto;
                    padding: 0 20px;
                    background-color: #f3f4f6;
                }}
                li {{
                    margin-bottom: 8px;
                }}
                strong {{
                    color: #111827;
                }}
                .card {{
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 10px 15px -3px rgba(0,0, 0, 0.05);
                }}
                h1 {{
                    color: #1e3a8a;
                    border-bottom: 2px solid #e2e8f0;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #2563eb;
                    margin-top: 35px;
                    border-bottom: 1px solid #e2e8f0;
                    padding-bottom: 8px;
                }}
                h3 {{
                    color: #1e293b;
                    margin-top: 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                th {{
                    background-color: #3b82f6;
                    color: white;
                    text-align: left;
                    font-weight: 600;
                    padding: 12px 15px;
                }}
                td {{
                    padding: 12px 15px;
                    border-bottom: 1px solid #e2e8f0;
                    font-size: 0.92rem;
                }}
                tr:hover td {{
                    background-color: rgba(0, 0, 0, 0.01);
                }}
                pre {{
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    padding: 15px;
                    border-radius: 6px;
                    overflow-x: auto;
                    font-family: monospace;
                    font-size: 0.85rem;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                {html_body}
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_page)

    def export_report(self, task_id: str):
        """
        Generates and exports a ZIP archive containing:
          - report.json: Full audit report JSON
          - report.xlsx: Styled Excel sheet with Test Cases & Defects tabs
          - screenshots/: Folder of referenced screenshot files
        """
        testcases = report_repo.load_report_json(task_id)
        if testcases is None:
            return JSONResponse(status_code=404, content={"detail": "Report JSON not found"})

        try:
            excel_file = report_repo.generate_excel_file(testcases)
        except Exception as e:
            logger.exception("Failed to generate Excel report")
            return JSONResponse(status_code=500, content={"detail": f"Error generating Excel report: {str(e)}"})

        try:
            zip_buffer = report_repo.create_zip_archive(task_id, testcases, excel_file)
        except Exception as e:
            logger.exception("Failed to compile ZIP archive")
            return JSONResponse(status_code=500, content={"detail": f"Error compiling ZIP: {str(e)}"})

        headers = {
            'Content-Disposition': f'attachment; filename="audit_report_{task_id}.zip"'
        }
        return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)

report_service = ReportService()
