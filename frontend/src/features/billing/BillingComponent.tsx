'use client'

import React, { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { billingService } from './billing.service'
import { authService } from '@/features/auth/auth.service'
import { notificationService } from '@/features/notifications/notification.service'
import { es as t } from '@/shared/i18n/es'
import { BillingHistoryItem, UserBillingInfo } from './types'
import { BillingStats, HistoryTable } from './components/BillingSubComponents'
import { VoucherForm } from './VoucherForm'

/**
 * BillingComponent
 * Advanced subscription management. 
 * Orchestrates sub-components for stats, vouchers, and transaction history.
 */
export const BillingComponent: React.FC = () => {
    const [user, setUser] = useState<UserBillingInfo | null>(null)
    const [unreadNotificationsCount, setUnreadNotificationsCount] = useState<number>(0)
    const [history, setHistory] = useState<BillingHistoryItem[]>([])
    const [isLoading, setIsLoading] = useState<boolean>(true)

    /**
     * Data fetching logic encapsulated for reuse (initial load + after redemption)
     */
    const fetchData = useCallback(async () => {
        try {
            const [profile, billingHistory, notifSummary] = await Promise.all([
                authService.getProfile(),
                billingService.getBillingHistory(),
                notificationService.getSummary()
            ])
            setUser(profile as UserBillingInfo)
            setHistory(billingHistory || [])
            setUnreadNotificationsCount(notifSummary.unread_count)
        } catch (error) {
            console.error('Error fetching billing data:', error)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchData()
        const interval = setInterval(() => {
            notificationService.getSummary().then(res => setUnreadNotificationsCount(res.unread_count))
        }, 30000)
        return () => clearInterval(interval)
    }, [fetchData])

    if (isLoading && !user) {
        return (
            <div className="min-h-screen bg-[#020617] flex items-center justify-center">
                <div className="h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-[#020617] text-white flex font-sans selection:bg-blue-500/30">
            {/* Sidebar */}
            <aside className="w-64 border-r border-white/5 bg-[#020617] flex flex-col sticky top-0 h-screen shrink-0">
                <div className="p-8">
                    <div className="flex items-center gap-3 mb-12">
                        <div className="h-9 w-9 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white shadow-xl shadow-blue-500/10">A</div>
                        <div>
                            <span className="block text-lg font-bold tracking-tight text-white leading-none">AjaxSecurFlow</span>
                            <span className="text-[9px] font-black uppercase tracking-[0.15em] text-gray-600">Industrial Security</span>
                        </div>
                    </div>

                    <nav className="space-y-1">
                        <Link href="/dashboard" className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-500 hover:text-white hover:bg-white/5 transition-all group">
                            <span className="text-base opacity-50 group-hover:opacity-100">📊</span>
                            <span className="text-sm font-bold tracking-tight">{t.dashboard.nav.dashboard}</span>
                        </Link>
                        <Link href="/billing" className="flex items-center gap-3 px-4 py-3 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/10 transition-all">
                            <span className="text-base opacity-100">💳</span>
                            <span className="text-sm font-bold tracking-tight">{t.dashboard.nav.subscription}</span>
                        </Link>
                    </nav>
                </div>

                <div className="mt-auto p-8 space-y-1">
                    <div className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-500 hover:text-white hover:bg-white/5 transition-all cursor-pointer">
                        <span className="text-base opacity-50">⚙️</span>
                        <span className="text-sm font-bold tracking-tight">{t.dashboard.nav.settings}</span>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 bg-[#020617] overflow-y-auto">
                <header className="h-20 border-b border-white/5 px-10 flex items-center justify-between sticky top-0 z-30 bg-[#020617]/80 backdrop-blur-xl">
                    <h2 className="text-lg font-bold tracking-tight">{t.dashboard.billing.title}</h2>
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2">
                            <p className="text-xs font-bold text-white">{user?.email}</p>
                            <div className="relative">
                                <span className="text-sm">🔔</span>
                                {unreadNotificationsCount > 0 && (
                                    <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-red-600 border border-[#020617] flex items-center justify-center text-[7px] font-bold text-white">
                                        {unreadNotificationsCount}
                                    </span>
                                )}
                            </div>
                        </div>
                        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 border border-white/10 flex items-center justify-center text-xs shadow-lg">👤</div>
                    </div>
                </header>

                <div className="p-10 max-w-[1200px] mx-auto space-y-10">
                    <div className="pb-2">
                        <p className="text-gray-500 text-sm">{t.dashboard.billing.description}</p>
                    </div>

                    <BillingStats user={user} />

                    <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl overflow-hidden flex flex-col md:flex-row items-stretch">
                        <div className="w-full md:w-1/3 bg-blue-600 flex items-center justify-center p-12 min-h-[160px]">
                            <span className="text-6xl drop-shadow-2xl">💵</span>
                        </div>
                        <div className="flex-1 p-8 flex flex-col md:flex-row items-center justify-between gap-6">
                            <div className="space-y-2">
                                <h3 className="text-xl font-bold flex items-center gap-2">
                                    <span className="text-blue-400">🛡️</span> {t.dashboard.billing.portal.title}
                                </h3>
                                <p className="text-gray-500 text-sm max-w-md">{t.dashboard.billing.portal.description}</p>
                            </div>
                            <button className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-8 rounded-xl transition-all shadow-lg shadow-blue-600/20 flex items-center gap-2 whitespace-nowrap">
                                <span>📤</span> {t.dashboard.billing.portal.button}
                            </button>
                        </div>
                    </div>

                    <VoucherForm onSuccess={fetchData} />

                    <div className="space-y-6">
                        <div className="flex justify-between items-end">
                            <h3 className="text-xl font-bold tracking-tight">{t.dashboard.billing.history.title}</h3>
                            <span className="text-[10px] font-black text-gray-600 uppercase tracking-widest">{t.dashboard.billing.history.lastEntries}</span>
                        </div>
                        <HistoryTable history={history} />
                        <div className="p-6 text-center">
                            <button className="text-[10px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-400 transition-colors">
                                {t.dashboard.billing.history.viewAll}
                            </button>
                        </div>
                    </div>

                    <footer className="pt-10 pb-4 flex flex-col items-center gap-4 opacity-30">
                        <div className="flex items-center gap-2 py-1 px-3 bg-white/5 rounded-lg border border-white/10 text-[10px] uppercase tracking-widest font-black">
                            <span>🔒</span> {t.dashboard.billing.footer.encrypted}
                        </div>
                        <p className="text-[9px] font-medium text-center">
                            {t.dashboard.billing.footer.rights}
                        </p>
                    </footer>
                </div>
            </main>
        </div>
    )
}
