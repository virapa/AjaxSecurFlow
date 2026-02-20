'use client'

import React from 'react'
import { StaticPageWrapper } from '@/shared/components/StaticPageWrapper'
import { es as t } from '@/shared/i18n/es'

export default function SecurityDisclosurePage() {
    return (
        <StaticPageWrapper
            title={t.legal.security.title}
            description={t.legal.security.lastUpdated}
        >
            <div className="space-y-12">
                <section>
                    <p className="text-gray-400 leading-relaxed text-lg">
                        {t.legal.security.introduction}
                    </p>
                </section>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {t.legal.security.measures.map((measure, idx) => (
                        <div key={idx} className="flex items-center gap-4 bg-white/5 border border-white/5 p-6 rounded-2xl transition-all hover:border-cyan-500/30">
                            <div className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.5)]" />
                            <span className="text-sm font-medium text-gray-300">{measure}</span>
                        </div>
                    ))}
                </div>

                <section className="bg-gradient-to-r from-cyan-600/20 to-blue-600/10 border-2 border-cyan-500/20 p-10 rounded-3xl text-center relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <span className="text-8xl">🛡️</span>
                    </div>
                    <h3 className="text-2xl font-bold mb-4 text-white">Reporte Responsable</h3>
                    <p className="text-gray-400 text-sm max-w-lg mx-auto mb-6">
                        {t.legal.security.contact}
                    </p>
                    <a
                        href="mailto:security@ajaxsecurflow.com"
                        className="inline-block px-8 py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-xl transition-all shadow-lg shadow-cyan-600/20"
                    >
                        Enviar Reporte
                    </a>
                </section>
            </div>
        </StaticPageWrapper>
    )
}
