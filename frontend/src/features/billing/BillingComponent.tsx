'use client'

import React, { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { Sidebar } from '@/features/navigation/Sidebar'
import { billingService } from './billing.service'
import { authService } from '@/features/auth/auth.service'
import { notificationService } from '@/features/notifications/notification.service'
import { es as t } from '@/shared/i18n/es'
import { BillingHistoryItem, UserBillingInfo } from './types'
import { BillingStats, HistoryTable, PricingTable } from './components/BillingSubComponents'
import { VoucherForm } from './VoucherForm'
import { DashboardHeader } from '@/features/navigation/DashboardHeader'

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

    const handleSubscribe = async (plan: string) => {
        try {
            const { url } = await billingService.createCheckoutSession(plan)
            window.location.href = url
        } catch (error) {
            console.error('Error creating checkout session:', error)
            alert('Error al iniciar el proceso de pago. Por favor, inténtelo de nuevo.')
        }
    }

    if (isLoading && !user) {
        // ... (rest of loading state)
        return (
            <div className="min-h-screen bg-[#020617] flex items-center justify-center">
                <div className="h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-[#020617] text-white flex font-sans selection:bg-blue-500/30">
            <Sidebar />

            {/* Main Content */}
            <main className="flex-1 bg-[#020617] overflow-y-auto">
                <DashboardHeader
                    title={t.dashboard.billing.title}
                    user={user}
                    unreadNotificationsCount={unreadNotificationsCount}
                />

                <div className="p-10 max-w-[1200px] mx-auto space-y-10">
                    <div className="pb-2">
                        <p className="text-gray-500 text-sm">{t.dashboard.billing.description}</p>
                    </div>

                    <BillingStats user={user} />

                    <PricingTable
                        currentPlan={user?.subscription_plan || 'free'}
                        onSubscribe={handleSubscribe}
                    />

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
