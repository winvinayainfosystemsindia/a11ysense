from app.services.allure_manager import AllureManager
from app.schemas.audit import AuditResult
import os

class ReportService:
    def __init__(self):
        results_dir = os.getenv("ALLURE_RESULTS_DIR", "storage/reports/allure-results")
        self.allure_manager = AllureManager(results_dir)

    async def create_audit_report(self, result: AuditResult, custom_task_id: str = None):
        """
        Coordinates the transformation of an AuditResult into a professional Allure report.
        """
        import uuid
        task_id = custom_task_id or str(uuid.uuid4())
        
        from common.config import get_audit_storage_path
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

report_service = ReportService()
