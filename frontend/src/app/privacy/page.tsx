'use client'

import React from 'react'
import { StaticPageWrapper } from '@/shared/components/StaticPageWrapper'
import { es as t } from '@/shared/i18n/es'

export default function PrivacyPage() {
    return (
        <StaticPageWrapper
            title={t.legal.privacy.title}
            description={t.legal.privacy.lastUpdated}
        >
            <div className="space-y-12">
                <section>
                    <p className="text-gray-400 leading-relaxed">
                        {t.legal.privacy.introduction}
                    </p>
                </section>

                <div className="grid gap-10">
                    {t.legal.privacy.sections.map((section, idx) => (
                        <section key={idx} className="bg-white/5 border border-white/5 p-8 rounded-3xl transition-all hover:bg-white/[0.07] hover:border-white/10 group">
                            <h2 className="text-xl font-bold mb-4 text-cyan-400">{section.title}</h2>
                            <p className="text-gray-400 text-sm leading-relaxed group-hover:text-gray-300">
                                {section.content}
                            </p>
                        </section>
                    ))}
                </div>

                <section className="bg-cyan-500/5 border border-cyan-500/10 p-8 rounded-3xl">
                    <h3 className="text-lg font-bold mb-3 text-cyan-300">Contacto de Privacidad</h3>
                    <p className="text-gray-400 text-sm">
                        Para cualquier solicitud relacionada con tus datos o para ejercer tus derechos de acceso, por favor contacta con
                        <span className="text-cyan-400 ml-1 font-mono">privacy@ajaxsecurflow.com</span>
                    </p>
                </section>
            </div>
        </StaticPageWrapper>
    )
}
