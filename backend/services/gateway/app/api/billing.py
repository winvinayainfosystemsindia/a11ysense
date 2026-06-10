from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.models import User, Organization, CreditTransaction
from common.auth.deps import get_current_user, require_role
from common.billing.billing_manager import billing_manager
from app.schemas.billing import TransactionSchema, BillingStatusResponse, TopupRequest

router = APIRouter(prefix="/api/billing", tags=["Billing & Subscriptions"])


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("/status", response_model=BillingStatusResponse)
async def get_billing_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches the subscription plan, credit balance, and transaction history for the user's organization.
    """
    org = db.query(Organization).filter_by(id=current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    txns = db.query(CreditTransaction).filter_by(organization_id=org.id).order_by(CreditTransaction.timestamp.desc()).limit(15).all()

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


@router.post("/topup")
async def purchase_credits_topup(
    req: TopupRequest,
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db)
):
    """
    Simulates a secure checkout and statefully adds credits to the workspace.
    Requires Admin privileges.
    """
    org_id = current_user.organization_id
    credits_map = {
        "starter": 1000,   # $10 -> 1000 credits
        "growth": 6000,    # $50 -> 6000 credits (bonus 1000)
        "enterprise": 30000 # $200 -> 30000 credits (bonus 10000)
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


@router.post("/toggle-pay-as-you-go")
async def toggle_pay_as_you_go(
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db)
):
    """
    Toggles the Pay-As-You-Go overage feature. Allows balance to go negative.
    Requires Admin privileges.
    """
    org = db.query(Organization).filter_by(id=current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    org.pay_as_you_go_enabled = not org.pay_as_you_go_enabled
    db.commit()

    return {
        "status": "success",
        "pay_as_you_go_enabled": org.pay_as_you_go_enabled,
        "message": f"Pay-As-You-Go has been {'enabled' if org.pay_as_you_go_enabled else 'disabled'} successfully."
    }
