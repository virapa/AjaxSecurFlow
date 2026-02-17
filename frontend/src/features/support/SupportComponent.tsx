'use client'

import React, { useState, useEffect } from 'react'
import { Sidebar } from '@/features/navigation/Sidebar'
import { es as t } from '@/shared/i18n/es'
import { apiClient } from '@/infrastructure/api-client'
import { authService } from '@/features/auth/auth.service'
import { notificationService } from '@/features/notifications/notification.service'
import { DashboardHeader } from '@/features/navigation/DashboardHeader'
import { User } from '@/shared/types'

const SupportComponent: React.FC = () => {
    const [user, setUser] = useState<User | null>(null)
    const [unreadNotificationsCount, setUnreadNotificationsCount] = useState<number>(0)
    const [formData, setFormData] = useState({
        subject: '',
        category: 'question',
        message: '',
        email_confirmation: true
    })
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle')

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const [profile, notifSummary] = await Promise.all([
                    authService.getProfile(),
                    notificationService.getSummary()
                ])
                setUser(profile as User)
                setUnreadNotificationsCount(notifSummary.unread_count)
            } catch (err) {
                console.error('Failed to fetch profile/notifications for support page:', err)
            }
        }
        fetchProfile()
    }, [])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsSubmitting(true)
        setStatus('idle')

        try {
            await apiClient.post('/support/contact', formData)
            setStatus('success')
            setFormData({
                subject: '',
                category: 'question',
                message: '',
                email_confirmation: true
            })
        } catch (error) {
            console.error('[Support] Error submitting contact form:', error)
            setStatus('error')
        } finally {
            setIsSubmitting(false)
        }
    }

    const categories = [
        { id: 'bug', label: t.support.form.categories.bug, icon: "🐛" },
        { id: 'question', label: t.support.form.categories.question, icon: "❓" },
        { id: 'feedback', label: t.support.form.categories.feedback, icon: "💬" },
        { id: 'other', label: t.support.form.categories.other, icon: "📝" }
    ]

    return (
        <div className="min-h-screen bg-[#020617] text-white flex font-sans selection:bg-cyan-500/30">
            <Sidebar />

            <main className="flex-1 bg-[#020617] overflow-y-auto">
                <DashboardHeader
                    title={t.support.title}
                    user={user}
                    unreadNotificationsCount={unreadNotificationsCount}
                />

                <div className="max-w-4xl mx-auto p-6 md:p-10 space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    {/* Header Section */}
                    <div className="text-center space-y-4">
                        <h1 className="text-4xl md:text-5xl font-black tracking-tighter text-white">
                            {t.support.title}
                        </h1>
                        <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed">
                            {t.support.description}
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {/* Stats / Info Sidebar */}
                        <div className="md:col-span-1 space-y-6">
                            <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-6 backdrop-blur-md">
                                <div className="w-12 h-12 bg-cyan-500/10 rounded-2xl flex items-center justify-center text-cyan-400 mb-4 text-2xl">
                                    💬
                                </div>
                                <h3 className="text-sm font-black uppercase tracking-widest text-white mb-2">Respuesta Rápida</h3>
                                <p className="text-xs text-gray-500 leading-relaxed">Nuestro equipo de soporte suele responder en menos de 24 horas laborables.</p>
                            </div>

                            <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-6 backdrop-blur-md">
                                <div className="w-12 h-12 bg-indigo-500/10 rounded-2xl flex items-center justify-center text-indigo-400 mb-4 text-2xl">
                                    ❔
                                </div>
                                <h3 className="text-sm font-black uppercase tracking-widest text-white mb-2">Cualquier Consulta</h3>
                                <p className="text-xs text-gray-500 leading-relaxed">Desde problemas técnicos hasta dudas sobre tu suscripción o sugerencias de mejora.</p>
                            </div>
                        </div>

                        {/* Form Section */}
                        <div className="md:col-span-2">
                            <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-8 backdrop-blur-md relative overflow-hidden">
                                {status === 'success' ? (
                                    <div className="text-center py-12 space-y-6 animate-in zoom-in-95 duration-500">
                                        <div className="w-20 h-20 bg-green-500/10 rounded-full flex items-center justify-center text-green-400 mx-auto text-4xl">
                                            ✅
                                        </div>
                                        <h2 className="text-2xl font-black tracking-tight text-white">{t.support.form.success}</h2>
                                        <button
                                            onClick={() => setStatus('idle')}
                                            className="px-8 py-3 bg-white/5 hover:bg-white/10 text-white rounded-2xl font-bold transition-all border border-white/10"
                                        >
                                            Enviar otro mensaje
                                        </button>
                                    </div>
                                ) : (
                                    <form onSubmit={handleSubmit} className="space-y-6">
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-black uppercase tracking-widest text-gray-600 px-1">
                                                {t.support.form.subject}
                                            </label>
                                            <input
                                                type="text"
                                                required
                                                placeholder="Ej: Problema al conectar el Hub"
                                                className="w-full bg-[#1e293b]/50 border border-white/5 rounded-2xl px-6 py-4 text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-500/50 transition-all font-medium"
                                                value={formData.subject}
                                                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                                            />
                                        </div>

                                        <div className="space-y-2">
                                            <label className="text-[10px] font-black uppercase tracking-widest text-gray-600 px-1">
                                                {t.support.form.category}
                                            </label>
                                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                                                {categories.map((cat) => (
                                                    <button
                                                        key={cat.id}
                                                        type="button"
                                                        onClick={() => setFormData({ ...formData, category: cat.id })}
                                                        className={`flex flex-col items-center justify-center gap-2 p-4 rounded-2xl border transition-all ${formData.category === cat.id
                                                            ? 'bg-cyan-500/10 border-cyan-500/50 text-cyan-400'
                                                            : 'bg-white/5 border-white/5 text-gray-500 hover:border-white/10 hover:bg-white/10'
                                                            }`}
                                                    >
                                                        <span className="text-xl">{cat.icon}</span>
                                                        <span className="text-[9px] font-black uppercase tracking-wider text-center">{cat.label}</span>
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="space-y-2">
                                            <label className="text-[10px] font-black uppercase tracking-widest text-gray-600 px-1">
                                                {t.support.form.message}
                                            </label>
                                            <textarea
                                                required
                                                rows={5}
                                                className="w-full bg-[#1e293b]/50 border border-white/5 rounded-2xl px-6 py-4 text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-500/50 transition-all font-medium resize-none"
                                                value={formData.message}
                                                onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                                            />
                                        </div>

                                        <div className="flex items-center gap-3 px-1">
                                            <input
                                                type="checkbox"
                                                id="confirmation"
                                                className="w-4 h-4 rounded border-gray-300 text-cyan-600 focus:ring-cyan-500 bg-[#1e293b]/50"
                                                checked={formData.email_confirmation}
                                                onChange={(e) => setFormData({ ...formData, email_confirmation: e.target.checked })}
                                            />
                                            <label htmlFor="confirmation" className="text-xs text-gray-500">
                                                {t.support.form.emailConfirmation}
                                            </label>
                                        </div>

                                        {status === 'error' && (
                                            <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4 flex items-center gap-3 text-red-400 animate-in shake duration-300">
                                                <span>⚠️</span>
                                                <span className="text-sm font-bold">{t.support.form.error}</span>
                                            </div>
                                        )}

                                        <button
                                            type="submit"
                                            disabled={isSubmitting}
                                            className={`w-full py-5 rounded-2xl font-black uppercase tracking-widest text-sm transition-all flex items-center justify-center gap-3 ${isSubmitting
                                                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                                : 'bg-white text-black hover:bg-cyan-400 hover:text-white group'
                                                }`}
                                        >
                                            {isSubmitting ? (
                                                <>
                                                    <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                                                    {t.support.form.sending}
                                                </>
                                            ) : (
                                                <>
                                                    {t.support.form.submit}
                                                    <span className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform">🚀</span>
                                                </>
                                            )}
                                        </button>
                                    </form>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}

export default SupportComponent
