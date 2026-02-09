'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { billingService } from './billing.service'
import { authService } from '@/features/auth/auth.service'
import { notificationService } from '@/features/notifications/notification.service'
import { es as t } from '@/shared/i18n/es'

/**
 * BillingComponent
 * Advanced subscription management matching the Stitch design.
 */
export const BillingComponent: React.FC = () => {
    const [user, setUser] = useState<any>(null)
    const [unreadNotificationsCount, setUnreadNotificationsCount] = useState<number>(0)
    const [voucherCode, setVoucherCode] = useState('')
    const [isProcessing, setIsProcessing] = useState(false)
    const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
    const [history, setHistory] = useState<any[]>([])

    const fetchData = async () => {
        try {
            const [profile, voucherHistory, notifSummary] = await Promise.all([
                authService.getProfile(),
                billingService.getBillingHistory(),
                notificationService.getSummary()
            ])
            setUser(profile)
            setHistory(voucherHistory || [])
            setUnreadNotificationsCount(notifSummary.unread_count)
        } catch (error) {
            console.error('Error fetching billing data:', error)
        }
    }

    useEffect(() => {
        fetchData()
        const interval = setInterval(() => {
            notificationService.getSummary().then(res => setUnreadNotificationsCount(res.unread_count))
        }, 30000)
        return () => clearInterval(interval)
    }, [])

    const handleRedeem = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!voucherCode.trim()) return

        setIsProcessing(true)
        setStatus(null)
        try {
            await billingService.redeemVoucher(voucherCode)
            setStatus({ type: 'success', message: t.dashboard.billing.voucher.success })
            setVoucherCode('')
            // Refresh data to show new plan/expiration and history
            await fetchData()
        } catch (err: any) {
            setStatus({ type: 'error', message: err.message || t.dashboard.billing.voucher.error })
        } finally {
            setIsProcessing(false)
        }
    }

    return (
        <div className="min-h-screen bg-[#020617] text-white flex font-sans selection:bg-blue-500/30">
            {/* Consistent Sidebar */}
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
                            <p className="text-xs font-bold text-white">{user?.email || 'Admin User'}</p>
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

                    {/* Top Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="bg-[#0f172a]/60 border border-white/5 rounded-3xl p-8 backdrop-blur-md relative overflow-hidden group">
                            <div className="flex items-start justify-between mb-4">
                                <div className="space-y-1">
                                    <p className="text-[10px] font-black uppercase tracking-widest text-gray-600 flex items-center gap-2">
                                        <span className="text-blue-500">🛡️</span> Current Plan
                                    </p>
                                    <h3 className="text-3xl font-black tracking-tight">
                                        {user?.subscription_active
                                            ? (t.dashboard.stats as any)[user.subscription_plan] || user.subscription_plan
                                            : t.dashboard.stats.free}
                                    </h3>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className={`h-2 w-2 rounded-full ${user?.subscription_active ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
                                <span className={`text-xs font-bold uppercase tracking-widest ${user?.subscription_active ? 'text-green-400' : 'text-red-400'}`}>
                                    {user?.subscription_active ? t.dashboard.stats.active : t.dashboard.stats.expired}
                                </span>
                            </div>
                        </div>

                        <div className="bg-[#0f172a]/60 border border-white/5 rounded-3xl p-8 backdrop-blur-md relative overflow-hidden group">
                            <div className="flex items-start justify-between mb-4">
                                <div className="space-y-1">
                                    <p className="text-[10px] font-black uppercase tracking-widest text-gray-600 flex items-center gap-2">
                                        <span className="text-blue-400">🕒</span> {user?.subscription_id ? t.dashboard.billing.nextRenewal : t.dashboard.billing.expiration}
                                    </p>
                                    <h3 className="text-3xl font-black tracking-tight font-mono">
                                        {user?.subscription_expires_at
                                            ? new Date(user.subscription_expires_at).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' })
                                            : t.dashboard.billing.noExpiration}
                                    </h3>
                                </div>
                            </div>
                            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">
                                {user?.subscription_active ? t.dashboard.billing.statusActive : t.dashboard.billing.statusExpired}
                            </p>
                        </div>
                    </div>

                    {/* Stripe Portal Card */}
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

                    {/* Voucher Section */}
                    <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-8">
                        <h3 className="text-xl font-bold mb-6">{t.dashboard.billing.voucher.title}</h3>
                        <form onSubmit={handleRedeem} className="flex flex-col md:flex-row gap-4">
                            <div className="flex-1 relative">
                                <input
                                    type="text"
                                    value={voucherCode}
                                    onChange={(e) => setVoucherCode(e.target.value.toUpperCase())}
                                    placeholder={t.dashboard.billing.voucher.placeholder}
                                    className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-sm font-mono tracking-widest focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-gray-600"
                                />
                                <span className="absolute right-6 top-1/2 -translate-y-1/2 opacity-30">🎫</span>
                            </div>
                            <button
                                type="submit"
                                disabled={isProcessing || !voucherCode.trim()}
                                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-black uppercase tracking-widest py-4 px-10 rounded-2xl transition-all flex items-center justify-center gap-3"
                            >
                                {isProcessing ? t.dashboard.billing.voucher.processing : (
                                    <><span>📥</span> {t.dashboard.billing.voucher.button}</>
                                )}
                            </button>
                        </form>
                        {status && (
                            <p className={`mt-4 text-xs font-bold uppercase tracking-wider ${status.type === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                                {status.message}
                            </p>
                        )}
                        <p className="mt-4 text-[10px] text-gray-600 italic">{t.dashboard.billing.voucher.hint}</p>
                    </div>

                    {/* History Table */}
                    <div className="space-y-6">
                        <div className="flex justify-between items-end">
                            <h3 className="text-xl font-bold tracking-tight">{t.dashboard.billing.history.title}</h3>
                            <span className="text-[10px] font-black text-gray-600 uppercase tracking-widest">{t.dashboard.billing.history.lastEntries}</span>
                        </div>
                        <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl overflow-hidden">
                            <table className="w-full text-left">
                                <thead>
                                    <tr className="border-b border-white/5">
                                        <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.billing.history.cols.date}</th>
                                        <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.billing.history.cols.type}</th>
                                        <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.billing.history.cols.description}</th>
                                        <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-gray-600">{t.dashboard.billing.history.cols.amount}</th>
                                        <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-gray-600 text-right">{t.dashboard.billing.history.cols.status}</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {history.map((item, idx) => (
                                        <tr key={idx} className="hover:bg-white/[0.02] transition-all group">
                                            <td className="px-8 py-5 text-sm text-gray-400 whitespace-nowrap">
                                                {new Date(item.date).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })}
                                            </td>
                                            <td className="px-8 py-5 text-xs font-bold whitespace-nowrap">
                                                {item.type === 'payment' ? t.dashboard.billing.history.types.payment : t.dashboard.billing.history.types.voucher}
                                            </td>
                                            <td className="px-8 py-5 text-sm text-white">
                                                <div className="flex flex-col">
                                                    <span>{item.description}</span>
                                                    {item.download_url && (
                                                        <a href={item.download_url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-blue-500 hover:underline mt-1 flex items-center gap-1">
                                                            <span>📄</span> {t.dashboard.billing.history.download}
                                                        </a>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-8 py-5 text-sm font-bold text-gray-300">{item.amount}</td>
                                            <td className="px-8 py-5 text-right">
                                                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest ${item.status === 'Pagado' || item.status === 'Aplicado' ? 'bg-green-500/10 text-green-400' : 'bg-gray-500/10 text-gray-500'}`}>
                                                    <span className={`h-1 w-1 rounded-full ${item.status === 'Pagado' || item.status === 'Aplicado' ? 'bg-green-500' : 'bg-gray-500'}`}></span>
                                                    {item.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                    {history.length === 0 && (
                                        <tr>
                                            <td colSpan={4} className="px-8 py-10 text-center text-gray-500 text-xs italic">
                                                No hay códigos canjeados recientemente.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                            <div className="p-6 border-t border-white/5 text-center">
                                <button className="text-[10px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-400 transition-colors">
                                    {t.dashboard.billing.history.download}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Footer */}
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
