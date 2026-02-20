'use client'

import React from 'react'
import { StaticPageWrapper } from '@/shared/components/StaticPageWrapper'
import { es as t } from '@/shared/i18n/es'

export default function TermsPage() {
    return (
        <StaticPageWrapper
            title={t.legal.terms.title}
            description={t.legal.terms.lastUpdated}
        >
            <div className="space-y-12">
                <div className="grid gap-10">
                    {t.legal.terms.sections.map((section, idx) => (
                        <section key={idx} className="bg-white/5 border border-white/5 p-8 rounded-3xl transition-all hover:bg-white/[0.07] hover:border-white/10 group">
                            <h2 className="text-xl font-bold mb-4 text-cyan-400">{section.title}</h2>
                            <p className="text-gray-400 text-sm leading-relaxed group-hover:text-gray-300">
                                {section.content}
                            </p>
                        </section>
                    ))}
                </div>

                <section className="text-center p-12 border-t border-white/5 mt-16">
                    <p className="text-xs text-gray-500 italic">
                        Al continuar utilizando los servicios de AjaxSecurFlow, confirmas que has leído y aceptas quedar vinculado por estos Términos de Servicio.
                    </p>
                </section>
            </div>
        </StaticPageWrapper>
    )
}
