from sqlalchemy.orm import Session
from sqlalchemy import func
from common.database.models import ErrorEventRecord

class AdminRepository:
    def get_total_errors(self, db: Session) -> int:
        return db.query(ErrorEventRecord).count()

    def get_critical_errors_count(self, db: Session) -> int:
        return db.query(ErrorEventRecord).filter_by(severity="critical").count()

    def get_standard_errors_count(self, db: Session) -> int:
        return db.query(ErrorEventRecord).filter_by(severity="error").count()

    def get_service_breakdown(self, db: Session) -> dict:
        breakdown_rows = (
            db.query(ErrorEventRecord.service_name, func.count(ErrorEventRecord.id))
            .group_by(ErrorEventRecord.service_name)
            .all()
        )
        return {row[0]: row[1] for row in breakdown_rows}

    def get_latest_errors(self, db: Session, limit: int = 50) -> list[ErrorEventRecord]:
        return (
            db.query(ErrorEventRecord)
            .order_by(ErrorEventRecord.created_at.desc())
            .limit(limit)
            .all()
        )

admin_repo = AdminRepository()
