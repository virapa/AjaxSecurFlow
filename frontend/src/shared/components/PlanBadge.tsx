'use client'

import React from 'react'
import { SubscriptionPlan, getPlanDisplayName, getPlanColor } from '@/shared/utils/permissions'

interface PlanBadgeProps {
    plan: SubscriptionPlan
    size?: 'sm' | 'md' | 'lg'
    className?: string
}

export const PlanBadge: React.FC<PlanBadgeProps> = ({
    plan,
    size = 'sm',
    className = ''
}) => {
    const color = getPlanColor(plan)
    const displayName = getPlanDisplayName(plan)

    const sizeClasses = {
        sm: 'px-2 py-0.5 text-[8px]',
        md: 'px-3 py-1 text-[10px]',
        lg: 'px-4 py-1.5 text-xs'
    }

    const colorClasses = {
        gray: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
        blue: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
        purple: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
        amber: 'bg-gradient-to-r from-amber-500/20 to-yellow-500/20 text-amber-400 border-amber-500/30'
    }

    return (
        <span
            className={`
        inline-flex items-center justify-center
        rounded-md border font-black uppercase tracking-widest
        ${sizeClasses[size]}
        ${colorClasses[color as keyof typeof colorClasses]}
        ${className}
      `}
        >
            {displayName}
        </span>
    )
}
