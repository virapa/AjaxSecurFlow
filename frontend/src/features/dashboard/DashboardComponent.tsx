'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Sidebar } from '@/features/navigation/Sidebar'
import { useRouter } from 'next/navigation'
import { HubList } from '@/features/hubs/HubList'
import { DeviceTelemetry, DeviceTelemetryRef } from '@/features/devices/DeviceTelemetry'
import { EventFeed } from '@/features/logs/EventFeed'
import { AnalyticsDashboard } from './AnalyticsDashboard'
import { hubService, Hub } from '@/features/hubs/hub.service'
import { authService } from '@/features/auth/auth.service'
import { notificationService } from '@/features/notifications/notification.service'

import { es as t } from '@/shared/i18n/es'
import { DashboardHeader } from '@/features/navigation/DashboardHeader'
import { UpgradePrompt } from '@/shared/components/UpgradePrompt'
import { canAccessFeature, SubscriptionPlan } from '@/shared/utils/permissions'

/**
 * DashboardComponent (Local Scope: Dashboard)
 * High-performance industrial dashboard matching the reference design.
 */
export const DashboardComponent: React.FC = () => {
    const [hubs, setHubs] = useState<Hub[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [selectedHub, setSelectedHub] = useState<Hub | null>(null)
    const [user, setUser] = useState<any>(null)
    const [unreadNotificationsCount, setUnreadNotificationsCount] = useState<number>(0)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const telemetryRef = useRef<DeviceTelemetryRef>(null)

    // Calculate user plan once for consistency
    const userPlan = (user?.subscription_active ? user?.subscription_plan : 'free') as SubscriptionPlan || 'free'

    const fetchProfile = useCallback(async () => {
        try {
            const data = await authService.getProfile()
            setUser(data)
        } catch (err: unknown) {
            console.error('Failed to fetch profile:', err)
        }
    }, [])

    const fetchHubs = useCallback(async () => {
        try {
            const data = await hubService.getHubs()
            setHubs(data)

            // Only auto-select first hub on initial load (when no hub is selected)
            if (!selectedHub && data.length > 0) {
                setSelectedHub(data[0])
            }
            // Note: We don't update selectedHub on refresh to avoid resetting user's selection
        } catch (err: unknown) {
            const error = err as Error
            setError(error.message || t.dashboard.stats.systemDegraded)
        } finally {
            setIsLoading(false)
        }
    }, [selectedHub])

    const fetchNotificationsSummary = useCallback(async () => {
        try {
            const summary = await notificationService.getSummary()
            setUnreadNotificationsCount(summary.unread_count)
        } catch (err) {
            console.error('Failed to fetch notifications summary:', err)
        }
    }, [])

    const handleManualRefresh = async () => {
        setIsRefreshing(true)
        try {
            // Re-fetch all critical data
            await Promise.all([
                fetchProfile(),
                fetchHubs(),
                fetchNotificationsSummary()
            ])
            // Artificial delay for visual feedback if it was too fast
            await new Promise(resolve => setTimeout(resolve, 600))
        } catch (err) {
            console.error('Manual refresh failed:', err)
        } finally {
            setIsRefreshing(false)
        }
    }

    useEffect(() => {
        fetchProfile()
        fetchHubs()
        fetchNotificationsSummary()
        // Removed polling - hubs are loaded once on mount
        // User can refresh page if they want updated data
    }, [fetchProfile, fetchHubs, fetchNotificationsSummary])

    const activeHubsCount = hubs.filter(h => h.online).length
    const totalHubsCount = hubs.length

    return (
        <div className="min-h-screen bg-[#020617] text-white flex font-sans selection:bg-blue-500/30">
            <Sidebar />

            {/* Main Content Area */}
            <main className="flex-1 bg-[#020617]">
                {/* Header / Top Bar */}
                <DashboardHeader
                    user={user}
                    unreadNotificationsCount={unreadNotificationsCount}
                    searchQuery={searchQuery}
                    setSearchQuery={setSearchQuery}
                    isRefreshing={isRefreshing}
                    onRefresh={handleManualRefresh}
                    activeHubsCount={activeHubsCount}
                    totalHubsCount={totalHubsCount}
                />

                <div className="p-10 space-y-10 max-w-[1600px] mx-auto">
                    {/* Stats Ribbon */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
                        <StatCard
                            label={t.dashboard.stats.activeHubs}
                            value={isLoading ? '--/--' : `${activeHubsCount}/${totalHubsCount}`}
                            trend={activeHubsCount === totalHubsCount ? t.dashboard.stats.allSystemsOnline : t.dashboard.stats.systemDegraded}
                            color={activeHubsCount === totalHubsCount ? 'green' : 'yellow'}
                            progress={totalHubsCount > 0 ? (activeHubsCount / totalHubsCount) * 100 : 0}
                        />

                        {/* Analytics Trends - Centered between stats */}
                        <div className="md:mt-0">
                            <AnalyticsDashboard hubId={selectedHub?.id} />
                        </div>

                        <StatCard
                            label={t.dashboard.stats.planStatus}
                            value={user ? (user.subscription_active ? (t.dashboard.stats as any)[user.subscription_plan] : t.dashboard.stats.free) : '...'}
                            trend={user?.subscription_active ? t.dashboard.stats.active : t.dashboard.stats.expired}
                            color={user?.subscription_active ? 'indigo' : 'yellow'}
                            special={t.dashboard.stats.manageBilling}
                            specialHref="/billing"
                            progress={user?.subscription_active ? 100 : 0}
                        />
                    </div>

                    <div className="grid grid-cols-12 gap-8">
                        {/* Middle Section: Hubs & Telemetry */}
                        <div className="col-span-12 lg:col-span-8 space-y-10">
                            <div>
                                <div className="flex justify-between items-end mb-6">
                                    <h3 className="text-xl font-bold tracking-tight">{t.dashboard.hubs.title}</h3>
                                    <button
                                        onClick={() => setSearchQuery('')}
                                        className="text-[11px] font-bold text-blue-500 hover:text-blue-400 transition-colors uppercase tracking-widest"
                                    >
                                        {t.dashboard.hubs.viewAll}
                                    </button>
                                </div>
                                <HubList
                                    hubs={hubs}
                                    isLoading={isLoading}
                                    error={error}
                                    onSelectHub={setSelectedHub}
                                    refreshHubs={fetchHubs}
                                    selectedHubId={selectedHub?.id}
                                    searchQuery={searchQuery}
                                    userPlan={userPlan}
                                />
                            </div>

                            <div>
                                <div className="flex justify-between items-end mb-6">
                                    <h3 className="text-xl font-bold tracking-tight">
                                        {t.dashboard.telemetry.title} {selectedHub ? `(${selectedHub.name})` : ''}
                                    </h3>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => telemetryRef.current?.exportToCSV()}
                                            className="h-8 w-8 rounded-lg border border-white/10 bg-white/5 flex items-center justify-center text-xs hover:bg-white/10 transition-colors"
                                            title="Exportar Reporte CSV"
                                        >
                                            📥
                                        </button>
                                    </div>
                                </div>
                                {selectedHub ? (
                                    canAccessFeature(userPlan, 'read_devices') ? (
                                        <DeviceTelemetry
                                            ref={telemetryRef}
                                            hubId={selectedHub.id}
                                            searchQuery={searchQuery}
                                        />
                                    ) : (
                                        <div
                                            data-testid="restricted-telemetry"
                                            className="relative min-h-[500px] w-full block bg-[#0f172a]/40 border border-white/5 rounded-3xl overflow-hidden"
                                            style={{ width: '100%', minHeight: '500px' }}
                                        >
                                            <UpgradePrompt
                                                feature="Telemetría de Dispositivos"
                                                requiredPlan="basic"
                                                currentPlan={userPlan}
                                                className="w-full h-full"
                                            />
                                        </div>
                                    )
                                ) : (
                                    <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-12 text-center text-gray-500 italic text-xs">
                                        Seleccione hub para mas detalles
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Right Section: Event Feed */}
                        <div className="col-span-12 lg:col-span-4 h-full">
                            {selectedHub ? (
                                canAccessFeature(userPlan, 'read_logs') ? (
                                    <EventFeed hubId={selectedHub.id} role={selectedHub.role} />
                                ) : (
                                    <div
                                        data-testid="restricted-events"
                                        className="relative min-h-[600px] h-full w-full block bg-[#0f172a]/40 border border-white/5 rounded-3xl overflow-hidden"
                                        style={{ width: '100%', minHeight: '600px' }}
                                    >
                                        <UpgradePrompt
                                            feature="Historial de Eventos"
                                            requiredPlan="basic"
                                            currentPlan={userPlan}
                                            className="w-full h-full"
                                        />
                                    </div>
                                )
                            ) : (
                                <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-8 text-center text-gray-500 italic text-xs h-full flex items-center justify-center min-h-[400px]">
                                    Seleccione hub para mas detalles
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}

/** Helper Components for Cleaner Main Logic **/


interface StatCardProps {
    label: string;
    value: string | number;
    trend?: string;
    color?: string;
    special?: string;
    specialHref?: string;
    progress?: number;
}

const StatCard = ({ label, value, trend, color, special, specialHref, progress = 65 }: StatCardProps) => (
    <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-6 backdrop-blur-md">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-600 mb-4">{label}</p>
        <div className="flex items-baseline gap-3 mb-4">
            <h4 className="text-3xl font-black tracking-tighter">{value}</h4>
            <span className={`text-[11px] font-bold ${color === 'green' ? 'text-green-500/80' : color === 'yellow' ? 'text-yellow-500' : 'text-gray-500'}`}>{trend}</span>
        </div>
        <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
            <div
                className={`h-full rounded-full animate-in slide-in-from-left duration-1000 ${color === 'green' ? 'bg-green-500' :
                    color === 'blue' ? 'bg-blue-600' :
                        color === 'cyan' ? 'bg-cyan-400' :
                            color === 'yellow' ? 'bg-yellow-500' : 'bg-indigo-600'
                    }`}
                style={{ width: `${progress}%` }}
            />
        </div>
        {special && (
            specialHref ? (
                <Link href={specialHref} className="mt-4 block text-[9px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-400 transition-colors">
                    {special}
                </Link>
            ) : (
                <button className="mt-4 text-[9px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-400 transition-colors">{special}</button>
            )
        )}
    </div>
)
