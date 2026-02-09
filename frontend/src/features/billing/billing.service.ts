import { apiClient } from '@/infrastructure/api-client'

/**
 * Billing Service (Local Scope: features/billing)
 * Handles subscription and voucher logic.
 */
export const billingService = {
    /**
     * Redeems a voucher code to activate or extend subscription.
     * @param code The voucher code (e.g., AJAX-XXXX-XXXX)
     */
    redeemVoucher: async (code: string): Promise<{ status: string; message: string }> => {
        return apiClient.post<{ status: string; message: string }>('/billing/vouchers/redeem', {
            code: code
        })
    },

    /**
     * Creates a Stripe Checkout session.
     * @param priceId The Stripe price ID for the plan.
     */
    createCheckoutSession: async (priceId: string): Promise<{ url: string }> => {
        return apiClient.post<{ url: string }>('/billing/create-checkout-session', {
            price_id: priceId
        })
    },

    /**
     * Retrieves the unified billing history (payments and vouchers).
     */
    getBillingHistory: async (): Promise<any[]> => {
        return apiClient.get<any[]>('/billing/history')
    }
}
