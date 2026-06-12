from fastapi import HTTPException
from sqlalchemy.orm import Session
from common.database.models import User
from common.billing.billing_manager import billing_manager
from app.repository.billing_repo import billing_repo
from app.schemas.billing import TransactionSchema, BillingStatusResponse, TopupRequest

class BillingService:
    def get_billing_status(self, current_user: User, db: Session) -> BillingStatusResponse:
        org = billing_repo.get_organization_by_id(db, current_user.organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found.")

        txns = billing_repo.get_credit_transactions(db, org.id, limit=15)

        formatted_txns = []
        for t in txns:
            formatted_txns.append(
                TransactionSchema(
                    id=str(t.id),
                    amount=t.amount,
                    transaction_type=t.transaction_type,
                    description=t.description,
                    reference_id=t.reference_id,
                    timestamp=t.timestamp.isoformat()
                )
            )

        return BillingStatusResponse(
            plan_tier=org.plan_tier or "free",
            credit_balance=org.credit_balance or 0,
            billing_status=org.billing_status or "active",
            pay_as_you_go_enabled=org.pay_as_you_go_enabled or False,
            transactions=formatted_txns
        )

    def purchase_credits_topup(self, req: TopupRequest, current_user: User, db: Session) -> dict:
        org_id = current_user.organization_id
        credits_map = {
            "starter": 1000,
            "growth": 6000,
            "enterprise": 30000
        }

        credits_to_add = credits_map.get(req.package_name.lower())
        if not credits_to_add:
            raise HTTPException(status_code=400, detail="Invalid topup package name.")

        try:
            new_balance = billing_manager.add_credits(
                db=db,
                org_id=org_id,
                credits_added=credits_to_add,
                transaction_type="purchase",
                description=f"Standard credit topup ({req.package_name.capitalize()} Pack - ${req.amount_usd:.2f})"
            )
            return {
                "status": "success",
                "message": f"Successfully purchased {credits_to_add} credits.",
                "new_balance": new_balance
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def toggle_pay_as_you_go(self, current_user: User, db: Session) -> dict:
        org_id = current_user.organization_id
        org = billing_repo.get_organization_by_id(db, org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found.")

        updated_org = billing_repo.update_pay_as_you_go(db, org_id, not org.pay_as_you_go_enabled)
        if not updated_org:
            raise HTTPException(status_code=404, detail="Organization not found.")

        return {
            "status": "success",
            "pay_as_you_go_enabled": updated_org.pay_as_you_go_enabled,
            "message": f"Pay-As-You-Go has been {'enabled' if updated_org.pay_as_you_go_enabled else 'disabled'} successfully."
        }

billing_service = BillingService()
