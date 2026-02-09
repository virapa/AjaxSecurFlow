import { apiClient } from '@/infrastructure/api-client'
import { BillingHistoryItem, CheckoutSessionResponse, VoucherRedeemResponse } from './types'

/**
 * Billing Service (Local Scope: features/billing)
 * Handles subscription and voucher logic.
 */
export const billingService = {
    /**
     * Redeems a voucher code to activate or extend subscription.
     * @param code The voucher code (e.g., AJAX-XXXX-XXXX)
     */
    redeemVoucher: async (code: string): Promise<VoucherRedeemResponse> => {
        return apiClient.post<VoucherRedeemResponse>('/billing/vouchers/redeem', {
            code: code
        })
    },

    /**
     * Creates a Stripe Checkout session.
     * @param priceId The Stripe price ID for the plan.
     */
    createCheckoutSession: async (priceId: string): Promise<CheckoutSessionResponse> => {
        return apiClient.post<CheckoutSessionResponse>('/billing/create-checkout-session', {
            price_id: priceId
        })
    },

    /**
     * Retrieves the unified billing history (payments and vouchers).
     */
    getBillingHistory: async (): Promise<BillingHistoryItem[]> => {
        return apiClient.get<BillingHistoryItem[]>('/billing/history')
    }
}
