from typing import Optional
from fastapi import APIRouter, HTTPException
import logging

from app.schemas.audit import AuditResult
from app.services.report_service import report_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate")
async def generate_report(result: AuditResult, task_id: Optional[str] = None):
    """
    Industry-standard Allure report generation.
    """
    return await report_service.create_audit_report(result, task_id)

@router.get("/report/{task_id}/screenshot/{filename}")
async def get_report_screenshot(task_id: str, filename: str):
    """
    Serves a captured defect screenshot for the given task.
    """
    return report_service.get_report_screenshot(task_id, filename)

@router.get("/report/{task_id}")
async def get_html_report(task_id: str):
    """
    Directly serves a HTML render of the compiled audit reports.
    """
    return report_service.get_html_report(task_id)

@router.get("/report/{task_id}/export")
async def export_report(task_id: str):
    """
    Generates and exports a ZIP archive containing:
      - report.json: Full audit report JSON
      - report.xlsx: Styled Excel sheet with Test Cases & Defects tabs
      - screenshots/: Folder of referenced screenshot files
    """
    return report_service.export_report(task_id)
