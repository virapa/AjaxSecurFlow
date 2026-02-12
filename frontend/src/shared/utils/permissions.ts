/**
 * Permission Utility
 * Checks feature access based on user's subscription plan
 */

export type SubscriptionPlan = 'free' | 'basic' | 'pro' | 'premium'

export type Feature =
    | 'list_hubs'
    | 'read_devices'
    | 'read_rooms'
    | 'read_groups'
    | 'read_logs'
    | 'send_commands'
    | 'access_proxy'

/**
 * Permission matrix matching backend policy
 */
const PLAN_PERMISSIONS: Record<SubscriptionPlan, Feature[]> = {
    free: [
        'list_hubs' // View hub list and details only
    ],
    basic: [
        'list_hubs',
        'read_devices',   // View device list and details
        'read_rooms',     // View room list and details
        'read_groups',    // View group list
        'read_logs'       // View event logs
    ],
    pro: [
        'list_hubs',
        'read_devices',
        'read_rooms',
        'read_groups',
        'read_logs',
        'send_commands'   // Send arm/disarm commands
    ],
    premium: [
        'list_hubs',
        'read_devices',
        'read_rooms',
        'read_groups',
        'read_logs',
        'send_commands',
        'access_proxy'    // Full API proxy access
    ]
}

/**
 * Feature to minimum required plan mapping
 */
const FEATURE_REQUIREMENTS: Record<Feature, SubscriptionPlan> = {
    list_hubs: 'free',
    read_devices: 'basic',
    read_rooms: 'basic',
    read_groups: 'basic',
    read_logs: 'basic',
    send_commands: 'pro',
    access_proxy: 'premium'
}

/**
 * Plan tier hierarchy for comparison
 */
const PLAN_HIERARCHY: Record<SubscriptionPlan, number> = {
    free: 0,
    basic: 1,
    pro: 2,
    premium: 3
}

/**
 * Check if user's plan allows access to a specific feature
 */
export function canAccessFeature(
    userPlan: SubscriptionPlan | undefined,
    feature: Feature
): boolean {
    const plan = userPlan || 'free'
    const allowedFeatures = PLAN_PERMISSIONS[plan] || []
    return allowedFeatures.includes(feature)
}

/**
 * Get the minimum required plan for a feature
 */
export function getRequiredPlan(feature: Feature): SubscriptionPlan {
    return FEATURE_REQUIREMENTS[feature] || 'free'
}

/**
 * Get all features available for a plan
 */
export function getPlanFeatures(plan: SubscriptionPlan): Feature[] {
    return PLAN_PERMISSIONS[plan] || []
}

/**
 * Check if a plan is higher tier than another
 */
export function isPlanHigherThan(
    plan1: SubscriptionPlan,
    plan2: SubscriptionPlan
): boolean {
    return PLAN_HIERARCHY[plan1] > PLAN_HIERARCHY[plan2]
}

/**
 * Get plan display name
 */
export function getPlanDisplayName(plan: SubscriptionPlan): string {
    const names: Record<SubscriptionPlan, string> = {
        free: 'Gratis',
        basic: 'Básico',
        pro: 'Pro',
        premium: 'Premium'
    }
    return names[plan] || 'Gratis'
}

/**
 * Get plan color for UI
 */
export function getPlanColor(plan: SubscriptionPlan): string {
    const colors: Record<SubscriptionPlan, string> = {
        free: 'gray',
        basic: 'blue',
        pro: 'purple',
        premium: 'amber'
    }
    return colors[plan] || 'gray'
}
