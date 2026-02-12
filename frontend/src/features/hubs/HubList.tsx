'use client'

import React, { useEffect, useState } from 'react'
import { Card } from '@/shared/components/Card'
import { Button } from '@/shared/components/Button'
import { PlanBadge } from '@/shared/components/PlanBadge'
import { hubService, Hub } from './hub.service'
import { canAccessFeature, SubscriptionPlan } from '@/shared/utils/permissions'
import { es as t } from '@/shared/i18n/es'

interface HubListProps {
    hubs: Hub[]
    isLoading: boolean
    error: string | null
    onSelectHub: (hub: Hub) => void
    refreshHubs: () => void
    selectedHubId?: string
    searchQuery?: string
    userPlan?: SubscriptionPlan
}

export const HubList: React.FC<HubListProps> = ({
    hubs,
    isLoading,
    error,
    onSelectHub,
    refreshHubs,
    selectedHubId,
    searchQuery = '',
    userPlan = 'free'
}) => {
    const [isActionLoading, setIsActionLoading] = useState<string | null>(null)
    const [mounted, setMounted] = useState(false)

    useEffect(() => {
        setMounted(true)
    }, [])

    const handleArmAction = async (e: React.MouseEvent, hubId: string, newState: 0 | 1 | 2) => {
        e.stopPropagation()

        // Check permission before executing command
        if (!canAccessFeature(userPlan, 'send_commands')) {
            console.warn('Command execution requires Pro plan or higher')
            return
        }

        console.log(`Action: Security command started for ${hubId} -> target state: ${newState}`)
        try {
            setIsActionLoading(hubId)
            await hubService.setArmState(hubId, newState)
            // Wait for 1.5s for the physical system to complete the transition
            await new Promise(resolve => setTimeout(resolve, 1500))
            // Manual refresh after successful command to confirm the state change
            await refreshHubs()
        } catch (err) {
            console.error('Failed to change arm state', err)
        } finally {
            setIsActionLoading(null)
        }
    }

    if (!mounted || isLoading) {
        return (
            <div className="flex gap-6">
                {[1, 2].map(i => (
                    <div key={i} className="w-full h-80 bg-white/[0.02] border border-white/5 rounded-2xl animate-pulse" />
                ))}
            </div>
        )
    }

    if (hubs.length === 0) {
        return (
            <Card className="text-center p-16 border-white/5 bg-white/[0.02]">
                <h3 className="text-white font-bold mb-2">{t.dashboard.hubs.empty}</h3>
                <p className="text-gray-500 text-sm">{t.dashboard.hubs.emptyHint}</p>
            </Card>
        )
    }

    const filteredHubs = hubs.filter(hub =>
        (hub.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (hub.hub_subtype || '').toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {filteredHubs.map((hub) => (
                <div
                    key={hub.id}
                    className="relative group cursor-pointer"
                    onClick={() => onSelectHub(hub)}
                >
                    {/* Main Hub Card */}
                    <div className={`bg-[#0f172a]/40 border rounded-3xl overflow-hidden backdrop-blur-sm transition-all hover:border-white/20 ${selectedHubId === hub.id ? 'border-blue-500/50 shadow-lg shadow-blue-500/10' : 'border-white/10'
                        }`}>
                        {/* Top Section with Illustration/Image Placeholder */}
                        <div className="h-44 relative bg-gradient-to-br from-blue-900/20 to-black/40 flex items-center justify-center overflow-hidden">
                            {/* Mock Illustration Shape */}
                            <div className="w-24 h-24 bg-gradient-to-tr from-blue-600/20 to-blue-400/30 rounded-3xl rotate-12 absolute -right-4 -top-4 blur-2xl" />

                            <div className="relative z-10 flex flex-col items-center">
                                <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center text-4xl mb-3 shadow-inner">
                                    {hub.hub_subtype?.includes('Hybrid') ? '🗄️' :
                                        hub.hub_subtype?.includes('PLUS') ? '🔘' : '⚪'}
                                </div>
                                <h4 className="text-xl font-bold text-white mb-0.5">{hub.name || 'Ajax Hub'}</h4>
                                <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest">
                                    {hub.hub_subtype?.replace(/_/g, ' ') || 'Central Panel'}
                                </p>
                            </div>

                            {/* Arm State Badge */}
                            <div className={`absolute top-4 right-4 px-3 py-1 rounded-md text-[10px] font-black uppercase tracking-widest ${hub.state === 'ARMED' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                                hub.state === 'NIGHT_MODE' ? 'bg-purple-500/20 text-purple-100 border border-purple-500/30' :
                                    'bg-green-500/20 text-green-400 border border-green-500/30'
                                }`}>
                                {hub.state === 'ARMED' ? t.dashboard.hubs.status.armed :
                                    hub.state === 'NIGHT_MODE' ? t.dashboard.hubs.status.night : t.dashboard.hubs.status.disarmed}
                            </div>

                            {/* Limited Functions Badge for non-PRO/MASTER users */}
                            {hub.role && hub.role !== 'MASTER' && hub.role !== 'PRO' && (
                                <div className="absolute top-4 left-4 px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[8px] font-black uppercase tracking-widest animate-pulse shadow-lg shadow-amber-500/10">
                                    ⚠️ {t.dashboard.hubs.limitedFunctions}
                                </div>
                            )}
                        </div>

                        {/* Mid Section: Telemetry Highlights */}
                        <div className="p-6 grid grid-cols-3 gap-2 border-y border-white/5">
                            <div className="text-center">
                                <span className="block text-[8px] uppercase text-gray-600 font-bold mb-1 tracking-widest">{t.dashboard.hubs.telemetry.connection}</span>
                                <span className={`text-[11px] font-bold ${hub.online ? 'text-white' : 'text-gray-500'}`}>
                                    {hub.online ? (hub.gsm?.activeSimCard !== undefined ? 'GSM + ETH' : 'Ethernet') : t.dashboard.hubs.status.offline}
                                </span>
                            </div>
                            <div className="text-center border-x border-white/5">
                                <span className="block text-[8px] uppercase text-gray-600 font-bold mb-1 tracking-widest">{t.dashboard.hubs.telemetry.signal}</span>
                                <span className={`text-[11px] font-bold ${hub.gsm?.signalLevel === 'STRONG' ? 'text-green-400' : 'text-yellow-500'}`}>
                                    {hub.gsm?.signalLevel || t.dashboard.hubs.telemetry.excellent}
                                </span>
                            </div>
                            <div className="text-center">
                                <span className="block text-[8px] uppercase text-gray-600 font-bold mb-1 tracking-widest">{t.dashboard.hubs.telemetry.battery}</span>
                                <span className="text-[11px] font-bold text-white">
                                    {hub.battery?.chargeLevelPercentage || hub.battery_level || 100}%
                                </span>
                            </div>
                        </div>

                        {/* Footer Section: Multi-State Controls */}
                        <div className="p-4 flex flex-col gap-3 bg-black/20">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className={`h-2 w-2 rounded-full ${hub.online ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                                        {hub.online ? t.dashboard.hubs.status.online : t.dashboard.hubs.status.offline}
                                    </span>
                                </div>
                                {isActionLoading === hub.id && (
                                    <span className="text-[9px] font-bold text-blue-500 animate-pulse uppercase">{t.dashboard.hubs.telemetry.sending}</span>
                                )}
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                                {/* Button Logic based on current state */}
                                {hub.state === 'ARMED' ? (
                                    <>
                                        <Button
                                            size="sm"
                                            disabled={isActionLoading === hub.id || !canAccessFeature(userPlan, 'send_commands')}
                                            onClick={(e) => handleArmAction(e, hub.id, 2)}
                                            className={`rounded-xl font-bold text-[9px] uppercase tracking-tighter bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/20 ${!canAccessFeature(userPlan, 'send_commands') ? 'opacity-50 cursor-not-allowed' : ''}`}
                                        >
                                            {t.dashboard.hubs.telemetry.nightMode}
                                        </Button>
                                        <Button
                                            size="sm"
                                            disabled={isActionLoading === hub.id || !canAccessFeature(userPlan, 'send_commands')}
                                            onClick={(e) => handleArmAction(e, hub.id, 0)}
                                            className={`rounded-xl font-bold text-[10px] uppercase tracking-tighter bg-white/5 hover:bg-white/10 text-white border-white/10 ${!canAccessFeature(userPlan, 'send_commands') ? 'opacity-50 cursor-not-allowed' : ''}`}
                                        >
                                            {t.dashboard.hubs.telemetry.disarm}
                                        </Button>
                                    </>
                                ) : hub.state === 'NIGHT_MODE' ? (
                                    <>
                                        <Button
                                            size="sm"
                                            disabled={isActionLoading === hub.id || !canAccessFeature(userPlan, 'send_commands')}
                                            onClick={(e) => handleArmAction(e, hub.id, 1)}
                                            className={`rounded-xl font-bold text-[9px] uppercase tracking-tighter bg-blue-600 hover:bg-blue-500 text-white border-0 shadow-lg shadow-blue-500/20 ${!canAccessFeature(userPlan, 'send_commands') ? 'opacity-50 cursor-not-allowed' : ''}`}
                                        >
                                            {t.dashboard.hubs.telemetry.armTotal}
                                        </Button>
                                        <Button
                                            size="sm"
                                            disabled={isActionLoading === hub.id || !canAccessFeature(userPlan, 'send_commands')}
                                            onClick={(e) => handleArmAction(e, hub.id, 0)}
                                            className={`rounded-xl font-bold text-[10px] uppercase tracking-tighter bg-white/5 hover:bg-white/10 text-white border-white/10 ${!canAccessFeature(userPlan, 'send_commands') ? 'opacity-50 cursor-not-allowed' : ''}`}
                                        >
                                            {t.dashboard.hubs.telemetry.disarm}
                                        </Button>
                                    </>
                                ) : (
                                    <>
                                        <Button
                                            size="sm"
                                            disabled={isActionLoading === hub.id || !canAccessFeature(userPlan, 'send_commands')}
                                            onClick={(e) => handleArmAction(e, hub.id, 1)}
                                            className={`rounded-xl font-bold text-[9px] uppercase tracking-tighter bg-blue-600 hover:bg-blue-500 text-white border-0 shadow-lg shadow-blue-500/20 ${!canAccessFeature(userPlan, 'send_commands') ? 'opacity-50 cursor-not-allowed' : ''}`}
                                        >
                                            {t.dashboard.hubs.telemetry.armTotal}
                                        </Button>
                                        <Button
                                            size="sm"
                                            disabled={isActionLoading === hub.id || !canAccessFeature(userPlan, 'send_commands')}
                                            onClick={(e) => handleArmAction(e, hub.id, 2)}
                                            className={`rounded-xl font-bold text-[9px] uppercase tracking-tighter bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/20 ${!canAccessFeature(userPlan, 'send_commands') ? 'opacity-50 cursor-not-allowed' : ''}`}
                                        >
                                            {t.dashboard.hubs.telemetry.nightMode}
                                        </Button>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    )
}
