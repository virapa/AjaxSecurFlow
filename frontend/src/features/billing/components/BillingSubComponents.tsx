import React from 'react';
import { BillingHistoryItem } from '../types';
import { es as t } from '@/shared/i18n/es';

interface HistoryTableProps {
    history: BillingHistoryItem[];
}

export const HistoryTable: React.FC<HistoryTableProps> = ({ history }) => {
    return (
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
                        <tr key={item.id || idx} className="hover:bg-white/[0.02] transition-all group">
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
                            <td colSpan={5} className="px-8 py-10 text-center text-gray-500 text-xs italic">
                                No hay registros de facturación recientemente.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};

interface BillingStatsProps {
    user: any;
}

export const BillingStats: React.FC<BillingStatsProps> = ({ user }) => {
    return (
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
    );
};
