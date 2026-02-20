'use client'

import React, { useState } from 'react'
import { StaticPageWrapper } from '@/shared/components/StaticPageWrapper'
import { es as t } from '@/shared/i18n/es'
import { apiClient } from '@/infrastructure/api-client'

export default function PublicSupportPage() {
    const [formData, setFormData] = useState({
        subject: '',
        category: 'question',
        message: '',
        email: '',
        email_confirmation: true
    })
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle')

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
                email: '',
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
        <StaticPageWrapper
            title={t.support.title}
            description={t.support.description}
        >
            <div className="grid md:grid-cols-3 gap-12 py-8">
                {/* Contact Info Sidebar */}
                <div className="md:col-span-1 space-y-6">
                    <div className="bg-white/5 border border-white/5 p-8 rounded-3xl backdrop-blur-md">
                        <div className="w-12 h-12 bg-cyan-500/10 rounded-2xl flex items-center justify-center text-cyan-400 mb-6 text-2xl">
                            💬
                        </div>
                        <h3 className="text-sm font-black uppercase tracking-widest text-white mb-3">Tiempo de Respuesta</h3>
                        <p className="text-xs text-gray-500 leading-relaxed">Nuestro equipo industrial opera 24/7 para incidencias críticas. Consultas generales respondidas en menos de 24h.</p>
                    </div>

                    <div className="bg-white/5 border border-white/5 p-8 rounded-3xl backdrop-blur-md">
                        <div className="w-12 h-12 bg-blue-500/10 rounded-2xl flex items-center justify-center text-blue-400 mb-6 text-2xl">
                            📍
                        </div>
                        <h3 className="text-sm font-black uppercase tracking-widest text-white mb-3">Sede Central</h3>
                        <p className="text-xs text-gray-500 leading-relaxed">Madrid, España<br />Infraestructura Distribuida Global</p>
                    </div>
                </div>

                {/* Form Section */}
                <div className="md:col-span-2">
                    <div className="bg-white/5 border border-white/5 p-10 rounded-3xl backdrop-blur-md relative overflow-hidden">
                        {status === 'success' ? (
                            <div className="text-center py-12 space-y-6">
                                <div className="w-20 h-20 bg-green-500/10 rounded-full flex items-center justify-center text-green-400 mx-auto text-4xl">
                                    ✅
                                </div>
                                <h2 className="text-2xl font-black tracking-tight text-white">{t.support.form.success}</h2>
                                <button
                                    onClick={() => setStatus('idle')}
                                    className="px-8 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl font-bold transition-all border border-white/10"
                                >
                                    Enviar otro mensaje
                                </button>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div className="grid sm:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black uppercase tracking-widest text-gray-600 px-1">
                                            Tu Email
                                        </label>
                                        <input
                                            type="email"
                                            required
                                            placeholder="nombre@empresa.com"
                                            className="w-full bg-white/5 border border-white/5 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-cyan-500/50 transition-all font-medium"
                                            value={formData.email}
                                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black uppercase tracking-widest text-gray-600 px-1">
                                            {t.support.form.subject}
                                        </label>
                                        <input
                                            type="text"
                                            required
                                            placeholder="Ej: Integración API"
                                            className="w-full bg-white/5 border border-white/5 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-cyan-500/50 transition-all font-medium"
                                            value={formData.subject}
                                            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                                        />
                                    </div>
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
                                        className="w-full bg-white/5 border border-white/5 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-cyan-500/50 transition-all font-medium resize-none"
                                        value={formData.message}
                                        onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                                    />
                                </div>

                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className={`w-full py-5 rounded-2xl font-black uppercase tracking-widest text-sm transition-all flex items-center justify-center gap-3 ${isSubmitting
                                        ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                        : 'bg-white text-black hover:bg-cyan-500 hover:text-white group'
                                        }`}
                                >
                                    {isSubmitting ? (
                                        <>
                                            <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                                            Enviando...
                                        </>
                                    ) : (
                                        <>
                                            Enviar mensaje industrial
                                            <span className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform">🚀</span>
                                        </>
                                    )}
                                </button>
                            </form>
                        )}
                    </div>
                </div>
            </div>
        </StaticPageWrapper>
    )
}
