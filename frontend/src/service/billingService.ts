import api from './api';

export interface Transaction {
  id: string;
  amount: number;
  transaction_type: string;
  description: string | null;
  reference_id: string | null;
  timestamp: string;
}

export interface BillingStatus {
  plan_tier: string;
  credit_balance: number;
  billing_status: string;
  pay_as_you_go_enabled: boolean;
  transactions: Transaction[];
}

export const billingService = {
  async getBillingStatus(): Promise<BillingStatus> {
    const response = await api.get('/api/billing/status');
    return response.data;
  },

  async purchaseCredits(packageName: string, amountUsd: number): Promise<{ status: string; message: string; new_balance: number }> {
    const response = await api.post('/api/billing/topup', {
      package_name: packageName,
      amount_usd: amountUsd
    });
    return response.data;
  },

  async togglePayAsYouGo(): Promise<{ status: string; pay_as_you_go_enabled: boolean; message: string }> {
    const response = await api.post('/api/billing/toggle-pay-as-you-go');
    return response.data;
  }
};
