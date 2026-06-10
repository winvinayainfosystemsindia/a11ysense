import uuid
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from common.database.models import Organization, CreditTransaction, Project, User

logger = logging.getLogger(__name__)

# --- Subscription Plans Matrix Configuration ---
PLAN_SPECIFICATIONS = {
    "free": {
        "max_projects": 1,
        "max_members": 2,
        "max_depth": 1,
        "api_keys": False,
        "advanced_agent": False,
        "label": "Free Tier"
    },
    "pro": {
        "max_projects": 10,
        "max_members": 10,
        "max_depth": 3,
        "api_keys": True,
        "advanced_agent": False,
        "label": "Professional Tier"
    },
    "enterprise": {
        "max_projects": 99999,
        "max_members": 99999,
        "max_depth": 99,
        "api_keys": True,
        "advanced_agent": True,
        "label": "Enterprise Tier"
    }
}


class BillingManager:
    """
    BillingManager implements all business logic for feature gating, 
    credit balance queries, and secure transactional credit logs.
    """

    @staticmethod
    def get_plan_specs(plan_tier: str) -> dict:
        """Returns plan details, falling back to free tier if invalid."""
        return PLAN_SPECIFICATIONS.get((plan_tier or "free").lower(), PLAN_SPECIFICATIONS["free"])

    @staticmethod
    def check_feature_access(db: Session, org_id: uuid.UUID, feature_name: str, value: int = None) -> None:
        """
        Validates feature limits (e.g. max_projects, max_members, max_depth) based on organization tier.
        Raises 402/403 HTTPException if workspace limits are breached.
        """
        org = db.query(Organization).filter_by(id=org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization workspace not found.")

        specs = BillingManager.get_plan_specs(org.plan_tier)

        if feature_name == "max_projects":
            current_projects = db.query(Project).filter_by(organization_id=org_id).count()
            if current_projects >= specs["max_projects"]:
                raise HTTPException(
                    status_code=402,
                    detail=f"Project limit ({specs['max_projects']}) reached for the {specs['label']}. Upgrade required."
                )

        elif feature_name == "max_members":
            current_members = db.query(User).filter_by(organization_id=org_id).count()
            if current_members >= specs["max_members"]:
                raise HTTPException(
                    status_code=402,
                    detail=f"Workspace member limit ({specs['max_members']}) reached for the {specs['label']}. Upgrade required."
                )

        elif feature_name == "max_depth" and value is not None:
            if value > specs["max_depth"]:
                raise HTTPException(
                    status_code=402,
                    detail=f"Crawl depth '{value}' exceeds limit of '{specs['max_depth']}' for {specs['label']}. Upgrade required."
                )

        elif feature_name == "api_keys":
            if not specs["api_keys"]:
                raise HTTPException(
                    status_code=402,
                    detail=f"CI/CD API key access is disabled for the {specs['label']}. Upgrade required."
                )

        elif feature_name == "advanced_agent":
            if not specs["advanced_agent"]:
                raise HTTPException(
                    status_code=402,
                    detail=f"Advanced multi-agent planning is disabled for the {specs['label']}. Upgrade required."
                )

    @staticmethod
    def has_sufficient_credits(db: Session, org_id: uuid.UUID, minimum_required: int = 10) -> bool:
        """
        Verifies if the workspace has sufficient credit balance or has Pay-As-You-Go toggled.
        Minimum credit default required to initiate audit is 10.
        """
        org = db.query(Organization).filter_by(id=org_id).first()
        if not org:
            return False

        if org.pay_as_you_go_enabled:
            return True

        balance = org.credit_balance if org.credit_balance is not None else 0
        return balance >= minimum_required

    @staticmethod
    def deduct_credits(db: Session, org_id: uuid.UUID, credits_spent: int, task_id: str, description: str) -> int:
        """
        Safely debits credit balance statefully inside a database transaction, 
        writing a CreditTransaction ledger record.
        Allows negative balance ONLY if Pay-As-You-Go is enabled, otherwise floors at 0.
        """
        org = db.query(Organization).filter_by(id=org_id).with_for_update().first()
        if not org:
            raise ValueError("Organization workspace not found.")

        balance = org.credit_balance if org.credit_balance is not None else 0

        # Prevent deduction if strictly 0 or negative without pay-as-you-go
        if balance <= 0 and not org.pay_as_you_go_enabled:
            logger.warning(f"Org {org_id} has exhausted credits, skipping overage deduction.")
            return balance

        final_amount = credits_spent
        # If pay-as-you-go is disabled, prevent falling below 0
        if not org.pay_as_you_go_enabled and (balance - credits_spent) < 0:
            final_amount = balance  # Deduct only what is left

        org.credit_balance = balance - final_amount

        # Write transaction log
        txn = CreditTransaction(
            organization_id=org_id,
            amount=-final_amount,
            transaction_type="usage",
            description=description,
            reference_id=task_id,
            timestamp=datetime.utcnow()
        )
        db.add(txn)
        db.commit()
        logger.info(f"Deducted {final_amount} credits from Org {org_id} for task {task_id}. New balance: {org.credit_balance}")
        return org.credit_balance

    @staticmethod
    def add_credits(db: Session, org_id: uuid.UUID, credits_added: int, transaction_type: str = "purchase", description: str = "") -> int:
        """
        Replenishes credits in the workspace statefully, logging transaction.
        """
        org = db.query(Organization).filter_by(id=org_id).with_for_update().first()
        if not org:
            raise ValueError("Organization workspace not found.")

        balance = org.credit_balance if org.credit_balance is not None else 0
        org.credit_balance = balance + credits_added

        txn = CreditTransaction(
            organization_id=org_id,
            amount=credits_added,
            transaction_type=transaction_type,
            description=description,
            timestamp=datetime.utcnow()
        )
        db.add(txn)
        db.commit()
        logger.info(f"Credited {credits_added} tokens to Org {org_id}. New balance: {org.credit_balance}")
        return org.credit_balance

    @staticmethod
    def grant_welcome_bonus(db: Session, org_id: uuid.UUID) -> int:
        """
        Grants a default 500 demo credits bonus on new organization registration.
        """
        return BillingManager.add_credits(
            db=db,
            org_id=org_id,
            credits_added=500,
            transaction_type="grant",
            description="Welcome Evaluation Credit Bonus"
        )


billing_manager = BillingManager()
