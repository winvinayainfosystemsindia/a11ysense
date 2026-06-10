export interface TopupRequest {
  package_name: string;
  amount_usd: number;
}

export interface BillingTransaction {
  id: string;
  amount: number;
  transaction_type: string;
  description?: string;
  reference_id?: string;
  timestamp: string;
}

export interface BillingStatus {
  plan_tier: string;
  credit_balance: number;
  billing_status: string;
  pay_as_you_go_enabled: boolean;
  transactions: BillingTransaction[];
}
