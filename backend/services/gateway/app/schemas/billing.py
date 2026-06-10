from typing import Optional
from pydantic import BaseModel

class TransactionSchema(BaseModel):
    id: str
    amount: int
    transaction_type: str
    description: Optional[str]
    reference_id: Optional[str]
    timestamp: str


class BillingStatusResponse(BaseModel):
    plan_tier: str
    credit_balance: int
    billing_status: str
    pay_as_you_go_enabled: bool
    transactions: list[TransactionSchema]


class TopupRequest(BaseModel):
    package_name: str  # "starter" | "growth" | "enterprise"
    amount_usd: float
