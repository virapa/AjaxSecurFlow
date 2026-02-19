import React from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Button } from '@/shared/components/Button'
import { es as t } from '@/shared/i18n/es'

/**
 * LandingPage Component (Local Scope: Landing)
 * Implements the premium design from the requested image in Spanish.
 */
export const LandingPage: React.FC = () => {
    return (
        <div className="min-h-screen bg-[#020617] text-white selection:bg-cyan-500/30">
            {/* Nav Header */}
            <header className="fixed top-0 z-50 w-full border-b border-white/5 bg-[#020617]/80 backdrop-blur-md">
                <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
                    <Link href="/" className="group transition-all">
                        <Image
                            src="/assets/Full_logo.png"
                            alt="AjaxSecurFlow"
                            width={180}
                            height={40}
                            className="h-10 w-auto object-contain brightness-110"
                        />
                    </Link>

                    <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
                        <Link href="#features" className="hover:text-white transition-colors">{t.common.features}</Link>
                        <Link href="#security" className="hover:text-white transition-colors">{t.common.security}</Link>
                        <Link href="#pricing" className="hover:text-white transition-colors">{t.common.pricing}</Link>
                    </nav>

                    <div className="flex items-center gap-4">
                        <Link href="/login" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">{t.common.login}</Link>
                        <Link href="/login">
                            <Button className="h-9 px-4 text-xs font-semibold">{t.common.getStarted}</Button>
                        </Link>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="relative flex flex-col items-center justify-center overflow-hidden pt-32 pb-20 px-4 text-center">
                <div className="absolute top-[-10%] left-1/2 -z-10 h-[500px] w-[800px] -translate-x-1/2 rounded-[100%] bg-cyan-500/10 blur-[120px]" />
                <div className="absolute bottom-0 left-1/2 -z-10 h-[300px] w-full -translate-x-1/2 bg-gradient-to-t from-cyan-600/5 to-transparent" />

                <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/5 px-3 py-1 text-[10px] font-medium tracking-widest text-cyan-400 uppercase">
                    <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
                    {t.landing.hero.badge}
                </div>

                <h1 className="mt-8 max-w-4xl text-5xl font-extrabold tracking-tight sm:text-7xl">
                    {t.landing.hero.titlePrimary} <br />
                    <span className="bg-gradient-to-r from-cyan-400 to-cyan-600 bg-clip-text text-transparent">
                        {t.landing.hero.titleSecondary}
                    </span> {t.landing.hero.titleTertiary}
                </h1>

                <p className="mt-6 max-w-2xl text-lg text-gray-400 leading-relaxed">
                    {t.landing.hero.description}
                </p>

                <div className="mt-10 flex flex-col sm:flex-row gap-4 items-center">
                    <Link href="/login">
                        <Button className="h-12 px-8 text-sm font-bold shadow-xl shadow-cyan-500/20 group">
                            {t.landing.hero.ctaStart}
                            <span className="ml-2 transition-transform group-hover:translate-x-1">→</span>
                        </Button>
                    </Link>
                </div>

                {/* Micro Stats */}
                <div className="mt-24 grid grid-cols-2 md:grid-cols-3 gap-12 text-center border-t border-white/5 pt-12">
                    <div className="flex flex-col items-center gap-2">
                        <div className="text-cyan-500">🛡️</div>
                        <span className="text-[10px] uppercase tracking-widest font-semibold text-gray-500">{t.landing.hero.encrypted}</span>
                    </div>
                    <div className="flex flex-col items-center gap-2">
                        <div className="text-cyan-500">🌐</div>
                        <span className="text-[10px] uppercase tracking-widest font-semibold text-gray-500">{t.landing.hero.distributed}</span>
                    </div>
                    <div className="hidden md:flex flex-col items-center gap-2">
                        <div className="text-cyan-500">⚡</div>
                        <span className="text-[10px] uppercase tracking-widest font-semibold text-gray-500">{t.landing.hero.realtime}</span>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="max-w-7xl mx-auto py-24 px-4 sm:px-6 lg:px-8">
                <div className="mb-16">
                    <h2 className="text-xs font-bold uppercase tracking-widest text-cyan-500 mb-2">{t.landing.capabilities.tag}</h2>
                    <h3 className="text-3xl font-bold tracking-tight">{t.landing.capabilities.title}</h3>
                    <p className="mt-4 max-w-xl text-gray-400 text-sm">{t.landing.capabilities.description}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {t.landing.capabilities.items.map((feature, idx) => (
                        <div key={idx} className="group relative rounded-2xl border border-white/5 bg-white/[0.02] p-8 transition-all hover:bg-white/[0.04]">
                            <div className="mb-6 flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-600/10 text-xl group-hover:bg-cyan-600/20 transition-colors">
                                {feature.icon}
                            </div>
                            <h4 className="text-lg font-bold mb-3">{feature.title}</h4>
                            <p className="text-sm text-gray-500 leading-relaxed">{feature.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Security Section */}
            <section id="security" className="max-w-7xl mx-auto py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-transparent via-cyan-600/5 to-transparent">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="h-48 rounded-2xl bg-gradient-to-br from-cyan-600/20 to-transparent border border-white/5 flex items-center justify-center text-4xl" title="Auditoría">📜</div>
                        <div className="h-64 rounded-2xl bg-gradient-to-tr from-white/5 to-transparent border border-white/5 mt-8 flex items-center justify-center text-4xl" title="Identidad">🔐</div>
                        <div className="h-64 rounded-2xl bg-gradient-to-bl from-white/5 to-transparent border border-white/5 -mt-8 flex items-center justify-center text-4xl" title="Infraestructura">🏭</div>
                        <div className="h-48 rounded-2xl bg-gradient-to-tl from-cyan-600/20 to-transparent border border-white/5 flex items-center justify-center text-4xl" title="Seguridad">🛡️</div>
                    </div>

                    <div>
                        <h2 className="text-4xl font-extrabold tracking-tight mb-6">
                            {t.landing.security.title} <span className="text-cyan-500">{t.landing.security.titleHighlight}</span> {t.landing.security.titleSuffix}
                        </h2>
                        <p className="text-gray-400 mb-10 leading-relaxed">{t.landing.security.description}</p>

                        <div className="space-y-8">
                            {t.landing.security.items.map((item, idx) => (
                                <div key={idx} className="flex gap-4">
                                    <div className="flex-shrink-0 h-6 w-6 rounded-full bg-cyan-600/20 flex items-center justify-center text-xs text-cyan-500">✓</div>
                                    <div>
                                        <h5 className="font-bold text-sm mb-1">{item.title}</h5>
                                        <p className="text-xs text-gray-500">{item.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* Pricing Section */}
            <section id="pricing" className="max-w-7xl mx-auto py-24 px-4 sm:px-6 lg:px-8 text-center">
                <h2 className="text-xs font-bold uppercase tracking-widest text-cyan-500 mb-4">{t.landing.pricing.tag}</h2>
                <h3 className="text-4xl font-extrabold tracking-tight mb-16">{t.landing.pricing.title}</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-7xl mx-auto">
                    {t.landing.pricing.plans.map((plan, idx) => (
                        <div
                            key={idx}
                            className={`relative rounded-3xl border p-8 text-left transition-all ${plan.recommended
                                ? 'border-cyan-500/50 bg-[#0ea5e9]/5 shadow-2xl shadow-cyan-500/10 scale-105'
                                : 'border-white/5 bg-white/[0.02] hover:border-white/10'
                                }`}
                        >
                            {plan.recommended && (
                                <div className="absolute top-0 right-1/2 translate-x-1/2 -translate-y-1/2 bg-cyan-500 text-[10px] font-bold uppercase tracking-widest px-4 py-1.5 rounded-full shadow-lg whitespace-nowrap">
                                    {plan.recommended}
                                </div>
                            )}

                            <span className={`text-xs font-bold uppercase tracking-wider ${plan.recommended ? 'text-cyan-400' : 'text-gray-500'}`}>
                                {plan.name}
                            </span>
                            <div className="mt-4 flex items-baseline gap-1">
                                <span className={`text-4xl font-extrabold ${plan.recommended ? 'text-cyan-400' : 'text-white'}`}>{plan.price}</span>
                                <span className="text-gray-500 text-sm">{plan.period}</span>
                            </div>
                            <p className="mt-4 mb-8 text-sm text-gray-400">{plan.desc}</p>

                            <ul className="space-y-4 mb-8">
                                {plan.features.map((feat, i) => (
                                    <li key={i} className={`flex items-center gap-3 text-sm ${plan.recommended ? 'text-cyan-400' : 'text-gray-400'}`}>
                                        <span className="text-cyan-500">✓</span> {feat}
                                    </li>
                                ))}
                            </ul>

                            <Link href="/login" className="w-full">
                                <Button
                                    variant={plan.recommended ? 'primary' : 'ghost'}
                                    className={`w-full ${!plan.recommended ? 'border border-white/10 hover:bg-white/5' : ''}`}
                                >
                                    {t.common.getStarted}
                                </Button>
                            </Link>
                        </div>
                    ))}
                </div>
            </section>

            {/* Footer */}
            <footer className="border-t border-white/5 py-12 px-4 sm:px-6 lg:px-8 mt-12 bg-black/50">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-12">
                    <div className="max-w-xs">
                        <div className="mb-4">
                            <Image
                                src="/assets/Full_logo.png"
                                alt="AjaxSecurFlow"
                                width={140}
                                height={32}
                                className="h-8 w-auto object-contain opacity-80 hover:opacity-100 transition-opacity"
                            />
                        </div>
                        <p className="text-xs text-gray-500 leading-relaxed">
                            {t.landing.footer.tagline}
                        </p>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-12">
                        <div>
                            <h6 className="text-xs font-bold uppercase tracking-widest text-white mb-4">{t.common.resources}</h6>
                            <ul className="text-xs text-gray-500 space-y-2">
                                {t.landing.footer.resources.map((item, idx) => (
                                    <li key={idx}>
                                        <Link
                                            href={
                                                item === t.landing.footer.resources[0] ? 'https://api.ajaxsecurflow.com/docs' :
                                                    item === t.landing.footer.resources[1] ? 'https://uptime.domoopen.es/status/ajaxsecurflow' : '/support'
                                            }
                                            target={
                                                (item === t.landing.footer.resources[0] || item === t.landing.footer.resources[1])
                                                    ? '_blank'
                                                    : undefined
                                            }
                                            rel="noopener noreferrer"
                                        >
                                            {item}
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div>
                            <h6 className="text-xs font-bold uppercase tracking-widest text-white mb-4">{t.common.legal}</h6>
                            <ul className="text-xs text-gray-500 space-y-2">
                                {t.landing.footer.legal.map((item, idx) => {
                                    const hrefs = ['/privacy', '/terms', '/security-disclosure'];
                                    return (
                                        <li key={idx}>
                                            <Link href={hrefs[idx] || '#'}>{item}</Link>
                                        </li>
                                    );
                                })}
                            </ul>
                        </div>
                    </div>
                </div>
                <div className="max-w-7xl mx-auto mt-12 pt-8 border-t border-white/5 flex justify-between items-center text-[10px] text-gray-600">
                    <p>{t.landing.footer.copyright}</p>
                    <div className="flex gap-4">
                        <Link href="https://github.com/virapa/AjaxSecurFlow" target="_blank" rel="noopener noreferrer">GitHub</Link>
                    </div>
                </div>
            </footer>
        </div>
    )
}
