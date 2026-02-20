'use client'

import React from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Button } from '@/shared/components/Button'
import { es as t } from '@/shared/i18n/es'

interface StaticPageWrapperProps {
    children: React.ReactNode
    title: string
    description?: string
}

export const StaticPageWrapper: React.FC<StaticPageWrapperProps> = ({ children, title, description }) => {
    return (
        <div className="min-h-screen bg-[#020617] text-white selection:bg-cyan-500/30 font-sans">
            {/* Nav Header (Same as Landing) */}
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
                        <Link href="/#features" className="hover:text-white transition-colors">{t.common.features}</Link>
                        <Link href="/#security" className="hover:text-white transition-colors">{t.common.security}</Link>
                        <Link href="/#pricing" className="hover:text-white transition-colors">{t.common.pricing}</Link>
                    </nav>

                    <div className="flex items-center gap-4">
                        <Link href="/login" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">{t.common.login}</Link>
                        <Link href="/login">
                            <Button className="h-9 px-4 text-xs font-semibold">{t.common.getStarted}</Button>
                        </Link>
                    </div>
                </div>
            </header>

            <main className="pt-32 pb-24 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
                {/* Hero Header for State Page */}
                <div className="relative mb-16">
                    <div className="absolute top-[-50%] left-1/2 -z-10 h-[300px] w-[500px] -translate-x-1/2 rounded-[100%] bg-cyan-500/10 blur-[100px]" />
                    <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4">
                        {title}
                    </h1>
                    {description && (
                        <p className="text-lg text-gray-400">
                            {description}
                        </p>
                    )}
                </div>

                {/* Content */}
                <div className="space-y-12">
                    {children}
                </div>
            </main>

            {/* Footer (Same as Landing) */}
            <footer className="border-t border-white/5 py-12 px-4 sm:px-6 lg:px-8 bg-black/50">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-12">
                    <div className="max-w-xs">
                        <div className="mb-4">
                            <Image
                                src="/assets/Full_logo.png"
                                alt="AjaxSecurFlow"
                                width={140}
                                height={32}
                                className="h-8 w-auto object-contain opacity-80"
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
