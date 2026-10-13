from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID
from common.database.models import EstimationRecord

class EstimationRepository:
    def list_estimations(self, db: Session, org_id: Optional[str] = None) -> List[EstimationRecord]:
        query = db.query(EstimationRecord)
        if org_id:
            try:
                org_uuid = uuid.UUID(org_id)
                query = query.filter((EstimationRecord.organization_id == org_uuid) | (EstimationRecord.organization_id.is_(None)))
            except (ValueError, TypeError):
                pass
        return query.order_by(EstimationRecord.created_at.desc()).all()

    def get_estimation(self, db: Session, estimate_id: str) -> Optional[EstimationRecord]:
        try:
            est_uuid = uuid.UUID(str(estimate_id))
        except (ValueError, TypeError):
            return None
        return db.query(EstimationRecord).filter(EstimationRecord.id == est_uuid).first()

    def create_estimation(
        self,
        db: Session,
        title: str,
        base_url: str,
        mode: str,
        pages: List[Dict[str, Any]],
        summary: Dict[str, Any],
        hourly_rate: float,
        platform_fee: float,
        profit_margin_pct: float,
        org_id: Optional[str] = None,
        status: str = "completed"
    ) -> EstimationRecord:
        org_uuid = None
        if org_id:
            try:
                org_uuid = uuid.UUID(str(org_id))
            except (ValueError, TypeError):
                org_uuid = None

        record = EstimationRecord(
            title=title or "Website Audit Estimation",
            base_url=base_url or (pages[0]["url"] if pages else "https://example.com"),
            mode=mode or "discover",
            status=status,
            hourly_rate=hourly_rate,
            platform_fee=platform_fee,
            profit_margin_pct=profit_margin_pct,
            total_pages=summary.get("total_pages", len(pages)),
            simple_pages=summary.get("simple_pages", 0),
            medium_pages=summary.get("medium_pages", 0),
            complex_pages=summary.get("complex_pages", 0),
            total_manual_hours=summary.get("total_manual_hours", 0.0),
            total_manual_cost=summary.get("total_manual_cost", 0.0),
            total_api_cost=summary.get("total_api_cost", 0.0),
            total_platform_cost=summary.get("total_platform_cost", 0.0),
            total_base_cost=summary.get("total_base_cost", 0.0),
            total_profit_margin=summary.get("total_profit_margin", 0.0),
            total_quote=summary.get("total_final_cost", 0.0),
            pages=pages,
            summary=summary,
            organization_id=org_uuid,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def update_estimation(
        self,
        db: Session,
        estimate_id: str,
        title: Optional[str] = None,
        pages: Optional[List[Dict[str, Any]]] = None,
        summary: Optional[Dict[str, Any]] = None,
        hourly_rate: Optional[float] = None,
        platform_fee: Optional[float] = None,
        profit_margin_pct: Optional[float] = None,
    ) -> Optional[EstimationRecord]:
        record = self.get_estimation(db, estimate_id)
        if not record:
            return None

        if title is not None:
            record.title = title
        if hourly_rate is not None:
            record.hourly_rate = hourly_rate
        if platform_fee is not None:
            record.platform_fee = platform_fee
        if profit_margin_pct is not None:
            record.profit_margin_pct = profit_margin_pct
        if pages is not None:
            record.pages = pages
        if summary is not None:
            record.summary = summary
            record.total_pages = summary.get("total_pages", len(pages or record.pages))
            record.simple_pages = summary.get("simple_pages", record.simple_pages)
            record.medium_pages = summary.get("medium_pages", record.medium_pages)
            record.complex_pages = summary.get("complex_pages", record.complex_pages)
            record.total_manual_hours = summary.get("total_manual_hours", record.total_manual_hours)
            record.total_manual_cost = summary.get("total_manual_cost", record.total_manual_cost)
            record.total_api_cost = summary.get("total_api_cost", record.total_api_cost)
            record.total_platform_cost = summary.get("total_platform_cost", record.total_platform_cost)
            record.total_base_cost = summary.get("total_base_cost", record.total_base_cost)
            record.total_profit_margin = summary.get("total_profit_margin", record.total_profit_margin)
            record.total_quote = summary.get("total_final_cost", record.total_quote)

        record.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(record)
        return record

    def delete_estimation(self, db: Session, estimate_id: str) -> bool:
        record = self.get_estimation(db, estimate_id)
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True

estimation_repo = EstimationRepository()
