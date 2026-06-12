from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.models import User
from common.auth.deps import get_current_user, require_role
from app.schemas.billing import BillingStatusResponse, TopupRequest
from app.services.billing_service import billing_service

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
    return billing_service.get_billing_status(current_user, db)


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
    return billing_service.purchase_credits_topup(req, current_user, db)


@router.post("/toggle-pay-as-you-go")
async def toggle_pay_as_you_go(
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db)
):
    """
    Toggles the Pay-As-You-Go overage feature. Allows balance to go negative.
    Requires Admin privileges.
    """
    return billing_service.toggle_pay_as_you_go(current_user, db)
