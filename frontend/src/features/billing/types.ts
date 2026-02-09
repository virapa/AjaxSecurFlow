/**
 * Supported transaction types in the billing history.
 */
export type BillingTransactionType = 'payment' | 'voucher';

/**
 * Represents a single entry in the unified billing history.
 */
export interface BillingHistoryItem {
    id: string;
    date: string; // ISO string from backend
    type: BillingTransactionType;
    description: string;
    amount?: string;
    status: string;
    download_url?: string;
}

/**
 * User billing data as returned by the auth/profile refresh.
 */
export interface UserBillingInfo {
    email: string;
    subscription_plan: 'free' | 'basic' | 'premium' | 'enterprise';
    subscription_active: boolean;
    subscription_id?: string;
    subscription_status?: string;
    subscription_expires_at?: string;
    stripe_customer_id?: string;
}

/**
 * API response for voucher redemption.
 */
export interface VoucherRedeemResponse {
    status: 'success' | 'error';
    message: string;
}

/**
 * API response for Stripe checkout session creation.
 */
export interface CheckoutSessionResponse {
    url: string;
}
