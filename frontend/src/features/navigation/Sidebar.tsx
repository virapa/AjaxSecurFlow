'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import Image from 'next/image'
import { es as t } from '@/shared/i18n/es'

/**
 * Sidebar Component (Local Scope: Navigation)
 * Primary navigation for the authenticated dashboard, unified across all pages.
 */
export const Sidebar: React.FC = () => {
    const pathname = usePathname()

    return (
        <aside className="w-64 border-r border-white/5 bg-[#020617] flex flex-col sticky top-0 h-screen shrink-0">
            <div className="p-8">
                <Link href="/dashboard" className="mb-12 group transition-all block">
                    <Image
                        src="/assets/Full_logo.png"
                        alt="AjaxSecurFlow"
                        width={220}
                        height={48}
                        className="h-12 w-auto object-contain hover:scale-105 transition-transform"
                    />
                </Link>

                <nav className="space-y-1">
                    <NavItem
                        icon="📊"
                        label={t.dashboard.nav.dashboard}
                        href="/dashboard"
                        active={pathname === '/dashboard'}
                    />
                    <NavItem
                        icon="🔔"
                        label={t.dashboard.nav.notifications}
                        href="/notifications"
                        active={pathname === '/notifications'}
                    />
                    <NavItem
                        icon="💳"
                        label={t.dashboard.nav.subscription}
                        href="/billing"
                        active={pathname === '/billing'}
                    />
                </nav>
            </div>

            <div className="mt-auto p-8 space-y-1">
                <NavItem
                    icon="⚙️"
                    label={t.dashboard.nav.settings}
                    href="/profile"
                    active={pathname === '/profile'}
                />
                <NavItem
                    icon="🎧"
                    label={t.dashboard.nav.support}
                    href="/support"
                    active={pathname === '/support'}
                />
            </div>
        </aside >
    )
}

/**
 * NavItem Helper
 * Consistent styling for sidebar links.
 */
const NavItem = ({ icon, label, href, active = false, badge }: { icon: string, label: string, href: string, active?: boolean, badge?: string }) => (
    <Link href={href} className={`flex items-center justify-between px-4 py-3 rounded-xl transition-all group ${active ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/10' : 'text-gray-500 hover:text-white hover:bg-white/5'}`}>
        <div className="flex items-center gap-3">
            <span className={`text-base ${active ? 'opacity-100' : 'opacity-50 group-hover:opacity-100'}`}>{icon}</span>
            <span className="text-sm font-bold tracking-tight">{label}</span>
        </div>
        {badge && (
            <span className="h-5 w-5 rounded-full bg-red-600 text-[10px] font-bold text-white flex items-center justify-center border-2 border-[#020617]">{badge}</span>
        )}
    </Link>
)
