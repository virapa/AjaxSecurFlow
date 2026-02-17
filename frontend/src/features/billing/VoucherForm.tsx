import React, { useState } from 'react'
import { billingService } from './billing.service'
import { es as t } from '@/shared/i18n/es'

interface VoucherFormProps {
    onSuccess: () => Promise<void>;
}

/**
 * VoucherForm Component (Local Scope: Billing)
 * Allows users to redeem activation codes with the premium Stitch design.
 */
export const VoucherForm: React.FC<VoucherFormProps> = ({ onSuccess }) => {
    const [voucherCode, setVoucherCode] = useState('')
    const [isProcessing, setIsProcessing] = useState(false)
    const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

    const handleRedeem = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!voucherCode.trim()) return

        setIsProcessing(true)
        setStatus(null)
        try {
            await billingService.redeemVoucher(voucherCode)
            setStatus({ type: 'success', message: t.dashboard.billing.voucher.success })
            setVoucherCode('')
            await onSuccess()
        } catch (err: unknown) {
            const error = err as Error;
            setStatus({ type: 'error', message: error.message || t.dashboard.billing.voucher.error })
        } finally {
            setIsProcessing(false)
        }
    }

    return (
        <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-8">
            <h3 className="text-xl font-bold mb-6">{t.dashboard.billing.voucher.title}</h3>
            <form onSubmit={handleRedeem} className="flex flex-col md:flex-row gap-4">
                <div className="flex-1 relative">
                    <input
                        type="text"
                        value={voucherCode}
                        onChange={(e) => setVoucherCode(e.target.value.toUpperCase())}
                        placeholder={t.dashboard.billing.voucher.placeholder}
                        aria-label={t.dashboard.billing.voucher.title}
                        className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-sm font-mono tracking-widest focus:outline-none focus:border-cyan-500/50 transition-all placeholder:text-gray-600"
                    />
                    <span className="absolute right-6 top-1/2 -translate-y-1/2 opacity-30">🎫</span>
                </div>
                <button
                    type="submit"
                    disabled={isProcessing || !voucherCode.trim()}
                    className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-black uppercase tracking-widest py-4 px-10 rounded-2xl transition-all flex items-center justify-center gap-3"
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
    )
}
