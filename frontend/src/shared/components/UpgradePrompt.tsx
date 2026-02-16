'use client'

import React from 'react'
import Link from 'next/link'
import { SubscriptionPlan, getPlanDisplayName } from '@/shared/utils/permissions'
import { PlanBadge } from './PlanBadge'

interface UpgradePromptProps {
    feature: string
    requiredPlan: SubscriptionPlan
    currentPlan: SubscriptionPlan
    className?: string
    compact?: boolean
}

const PLAN_PRICING: Record<SubscriptionPlan, string> = {
    free: '0€/mes',
    basic: '1€/mes',
    pro: '2€/mes',
    premium: '8€/mes'
}

export const UpgradePrompt: React.FC<UpgradePromptProps> = ({
    feature,
    requiredPlan,
    currentPlan,
    className = '',
    compact = false
}) => {
    if (compact) {
        return (
            <div className={`flex items-center justify-between p-4 bg-white/[0.02] border border-white/10 rounded-xl ${className}`}>
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center">
                        <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                    </div>
                    <div>
                        <p className="text-sm font-bold text-white">{feature}</p>
                        <p className="text-xs text-gray-500">
                            Requiere <PlanBadge plan={requiredPlan} size="sm" className="ml-1" />
                        </p>
                    </div>
                </div>
                <Link href="/billing">
                    <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition-colors">
                        Actualizar
                    </button>
                </Link>
            </div>
        )
    }

    return (
        <div className={`relative block w-full min-h-[400px] overflow-hidden ${className}`} style={{ width: '100%', minHeight: '400px' }}>
            {/* Backdrop blur overlay - slightly blue to pop from pure black */}
            <div className="absolute inset-0 backdrop-blur-xl bg-blue-950/40 z-10" />

            {/* Content */}
            <div className="absolute inset-0 z-20 flex items-center justify-center p-8 overflow-y-auto">
                <div className="max-w-md w-full bg-blue-900/40 border-2 border-blue-400/50 rounded-3xl p-10 text-center shadow-2xl shadow-blue-500/20 ring-1 ring-white/20 backdrop-blur-md">
                    {/* Lock Icon */}
                    <div className="w-16 h-16 mx-auto mb-4 bg-blue-500/20 rounded-2xl flex items-center justify-center">
                        <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                    </div>

                    {/* Title */}
                    <h3 className="text-2xl font-bold text-white mb-2">
                        Actualiza tu plan
                    </h3>

                    {/* Description */}
                    <p className="text-gray-400 mb-4">
                        <span className="font-semibold text-white">{feature}</span> requiere el plan{' '}
                        <PlanBadge plan={requiredPlan} size="md" className="mx-1" />
                    </p>

                    {/* Pricing */}
                    <div className="mb-6 p-4 bg-white/5 rounded-xl border border-white/10">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-gray-400">Plan actual:</span>
                            <PlanBadge plan={currentPlan} size="md" />
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-400">Plan requerido:</span>
                            <div className="flex items-center gap-2">
                                <PlanBadge plan={requiredPlan} size="md" />
                                <span className="text-sm font-bold text-white">
                                    {PLAN_PRICING[requiredPlan]}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* CTA Button */}
                    <Link href="/billing">
                        <button className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-xl transition-all shadow-lg shadow-blue-500/20">
                            Actualizar ahora
                        </button>
                    </Link>

                    {/* Features hint */}
                    <p className="mt-4 text-xs text-gray-500">
                        Desbloquea todas las funciones de {getPlanDisplayName(requiredPlan)}
                    </p>
                </div>
            </div>
        </div>
    )
}
