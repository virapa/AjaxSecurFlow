'use client'

import React, { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
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

/**
 * DashboardComponent (Local Scope: Dashboard)
 * High-performance industrial dashboard matching the reference design.
 */
export const DashboardComponent: React.FC = () => {
    const router = useRouter()
    const [hubs, setHubs] = useState<Hub[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [selectedHub, setSelectedHub] = useState<Hub | null>(null)
    const [user, setUser] = useState<any>(null)
    const [unreadNotificationsCount, setUnreadNotificationsCount] = useState<number>(0)
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
    const menuRef = useRef<HTMLDivElement>(null)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const telemetryRef = useRef<DeviceTelemetryRef>(null)

    const fetchProfile = async () => {
        try {
            const data = await authService.getProfile()
            setUser(data)
        } catch (err: any) {
            console.error('Failed to fetch profile:', err)
        }
    }

    const fetchHubs = async () => {
        try {
            const data = await hubService.getHubs()
            setHubs(data)

            // Only auto-select first hub on initial load (when no hub is selected)
            if (!selectedHub && data.length > 0) {
                setSelectedHub(data[0])
            }
            // Note: We don't update selectedHub on refresh to avoid resetting user's selection
        } catch (err: any) {
            setError(err.message || t.dashboard.stats.systemDegraded)
        } finally {
            setIsLoading(false)
        }
    }

    const fetchNotificationsSummary = async () => {
        try {
            const summary = await notificationService.getSummary()
            setUnreadNotificationsCount(summary.unread_count)
        } catch (err) {
            console.error('Failed to fetch notifications summary:', err)
        }
    }

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
    }, [])


    // Click outside handler for user menu
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsUserMenuOpen(false)
            }
        }
        document.addEventListener('click', handleClickOutside)
        return () => {
            document.removeEventListener('click', handleClickOutside)
        }
    }, [])

    const handleLogout = async (e?: React.MouseEvent) => {
        if (e) {
            e.preventDefault()
            e.stopPropagation()
        }

        localStorage.removeItem('ajax_access_token')
        document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT'

        try {
            await authService.logout()
        } catch (err) {
            console.warn('Network logout failed, proceeding with local cleanup:', err)
        } finally {
            window.location.href = '/'
        }
    }

    const activeHubsCount = hubs.filter(h => h.online).length
    const totalHubsCount = hubs.length

    return (
        <div className="min-h-screen bg-[#020617] text-white flex font-sans selection:bg-blue-500/30">
            <Sidebar />

            {/* Main Content Area */}
            <main className="flex-1 bg-[#020617]">
                {/* Header / Top Bar */}
                <header className="h-20 border-b border-white/5 px-10 flex items-center justify-between sticky top-0 z-30 bg-[#020617]/80 backdrop-blur-xl">
                    <div className="flex items-center gap-8">
                        <h2 className="text-lg font-bold tracking-tight">{t.dashboard.title}</h2>
                        <div className="relative group">
                            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-sm">🔍</span>
                            <input
                                type="text"
                                placeholder={t.dashboard.searchPlaceholder}
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="bg-white/5 border border-white/10 rounded-xl pl-12 pr-10 py-2.5 text-xs w-[320px] focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-gray-600"
                            />
                            {searchQuery && (
                                <button
                                    onClick={() => setSearchQuery('')}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors text-xs"
                                >
                                    ✕
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="px-4 py-1.5 rounded-full bg-white/5 border border-white/10 flex items-center gap-2">
                            {(() => {
                                const allOnline = activeHubsCount === totalHubsCount && totalHubsCount > 0;
                                const someOffline = activeHubsCount < totalHubsCount && totalHubsCount > 0;

                                if (allOnline) {
                                    return (
                                        <>
                                            <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
                                            <span className="text-[10px] font-bold uppercase tracking-widest text-green-400">
                                                {t.dashboard.systemStatus.secure}
                                            </span>
                                        </>
                                    );
                                } else {
                                    return (
                                        <>
                                            <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                                            <span className="text-[10px] font-bold uppercase tracking-widest text-red-500">
                                                {t.dashboard.systemStatus.attention}
                                            </span>
                                        </>
                                    );
                                }
                            })()}
                        </div>
                        <button
                            onClick={handleManualRefresh}
                            disabled={isRefreshing}
                            className={`text-gray-500 hover:text-white transition-all transform active:scale-95 ${isRefreshing ? 'opacity-50' : ''}`}
                            title={t.dashboard.nav.dashboard}
                        >
                            <span className={`inline-block ${isRefreshing ? 'animate-spin' : ''}`}>🔄</span>
                        </button>
                        <div className="h-10 w-[1px] bg-white/10 mx-2" />

                        {/* User Profile with Dropdown */}
                        <div className="flex items-center gap-3 relative" ref={menuRef}>
                            <button
                                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                                className="flex items-center gap-3 hover:bg-white/5 p-2 rounded-2xl transition-all"
                            >
                                <div className="text-right hidden sm:block">
                                    <div className="flex items-center gap-2">
                                        <p className="text-xs font-bold text-white">
                                            {user?.ajax_info?.firstName || t.dashboard.profile.adminUser}
                                        </p>
                                        <div className="relative">
                                            <span className="text-sm">🔔</span>
                                            {unreadNotificationsCount > 0 && (
                                                <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-red-600 border border-[#020617] flex items-center justify-center text-[7px] font-bold text-white">
                                                    {unreadNotificationsCount}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <p className="text-[9px] font-medium text-gray-500 text-left">
                                        {user?.ajax_info?.login || t.dashboard.profile.role}
                                    </p>
                                </div>
                                <div className="h-10 w-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 border border-white/10 flex items-center justify-center text-xs shadow-lg overflow-hidden">
                                    {user?.ajax_info?.imageUrls?.small ? (
                                        <img
                                            src={user.ajax_info.imageUrls.small}
                                            alt="Profile"
                                            className="w-full h-full object-cover"
                                            onError={(e) => {
                                                const target = e.target as HTMLImageElement;
                                                target.style.display = 'none';
                                                if (target.parentElement) {
                                                    target.parentElement.textContent = '👤';
                                                }
                                            }}
                                        />
                                    ) : (
                                        '👤'
                                    )}
                                </div>
                            </button>

                            {/* Dropdown Menu */}
                            {isUserMenuOpen && (
                                <div className="absolute right-0 top-full mt-2 w-48 bg-[#0f172a] border border-white/10 rounded-2xl shadow-2xl z-50 py-2 overflow-hidden animate-in fade-in zoom-in duration-200">
                                    <Link href="/profile" className="flex items-center gap-2 px-4 py-3 text-xs font-bold text-gray-400 hover:text-white hover:bg-white/5 transition-colors">
                                        <span>⚙️</span> {t.dashboard.nav.settings}
                                    </Link>
                                    <div className="h-px bg-white/5 my-1" />
                                    <button
                                        onMouseDown={(e) => {
                                            e.stopPropagation()
                                            handleLogout(e as any)
                                        }}
                                        className="w-full h-full flex items-center gap-2 px-4 py-3 text-xs font-bold text-red-100 bg-red-500/10 hover:bg-red-500/20 transition-all text-left z-[60]"
                                    >
                                        <span>🚪</span> {t.dashboard.nav.logout}
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </header>

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
                                    <DeviceTelemetry
                                        ref={telemetryRef}
                                        hubId={selectedHub.id}
                                        searchQuery={searchQuery}
                                    />
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
                                <EventFeed hubId={selectedHub.id} />
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


const StatCard = ({ label, value, trend, color, special, specialHref, progress = 65 }: any) => (
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
