import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.repository.admin_repo import admin_repo

class AdminService:
    def get_admin_errors_stats(self, db: Session) -> dict:
        total_errors = admin_repo.get_total_errors(db)
        critical_count = admin_repo.get_critical_errors_count(db)
        error_count = admin_repo.get_standard_errors_count(db)
        service_breakdown = admin_repo.get_service_breakdown(db)
        logs = admin_repo.get_latest_errors(db, 50)

        latest_logs = []
        for log in logs:
            context_str = "{}"
            if log.context_json:
                if isinstance(log.context_json, (dict, list)):
                    context_str = json.dumps(log.context_json)
                else:
                    context_str = str(log.context_json)

            latest_logs.append({
                "id": str(log.id),
                "correlation_id": log.correlation_id or "N/A",
                "service_name": log.service_name,
                "severity": log.severity,
                "message": log.message,
                "timestamp": log.timestamp.isoformat() if log.timestamp else datetime.utcnow().isoformat(),
                "context_json": context_str
            })

        return {
            "total_errors": total_errors,
            "critical_count": critical_count,
            "error_count": error_count,
            "service_breakdown": service_breakdown,
            "latest_logs": latest_logs
        }

admin_service = AdminService()
