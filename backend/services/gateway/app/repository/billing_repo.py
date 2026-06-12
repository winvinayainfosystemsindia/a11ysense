from sqlalchemy.orm import Session
from common.database.models import Organization, CreditTransaction

class BillingRepository:
    def get_organization_by_id(self, db: Session, org_id: str) -> Organization | None:
        return db.query(Organization).filter_by(id=org_id).first()

    def get_credit_transactions(self, db: Session, org_id: str, limit: int = 15) -> list[CreditTransaction]:
        return (
            db.query(CreditTransaction)
            .filter_by(organization_id=org_id)
            .order_by(CreditTransaction.timestamp.desc())
            .limit(limit)
            .all()
        )

    def update_pay_as_you_go(self, db: Session, org_id: str, enabled: bool) -> Organization | None:
        org = db.query(Organization).filter_by(id=org_id).first()
        if org:
            org.pay_as_you_go_enabled = enabled
            db.commit()
            db.refresh(org)
        return org

billing_repo = BillingRepository()
