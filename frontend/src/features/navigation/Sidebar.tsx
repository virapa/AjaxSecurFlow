'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
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
                <div className="flex items-center gap-3 mb-12">
                    <div className="h-9 w-9 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white shadow-xl shadow-blue-500/10">A</div>
                    <div>
                        <span className="block text-lg font-bold tracking-tight text-white leading-none">AjaxSecurFlow</span>
                        <span className="text-[9px] font-black uppercase tracking-[0.15em] text-gray-600">Industrial Security</span>
                    </div>
                </div>

                <nav className="space-y-1">
                    <NavItem
                        icon="📊"
                        label={t.dashboard.nav.dashboard}
                        href="/dashboard"
                        active={pathname === '/dashboard'}
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
        </aside>
    )
}

/**
 * NavItem Helper
 * Consistent styling for sidebar links.
 */
const NavItem = ({ icon, label, href, active = false, badge }: { icon: string, label: string, href: string, active?: boolean, badge?: string }) => (
    <Link href={href} className={`flex items-center justify-between px-4 py-3 rounded-xl transition-all group ${active ? 'bg-blue-500/10 text-blue-400 border border-blue-500/10' : 'text-gray-500 hover:text-white hover:bg-white/5'}`}>
        <div className="flex items-center gap-3">
            <span className={`text-base ${active ? 'opacity-100' : 'opacity-50 group-hover:opacity-100'}`}>{icon}</span>
            <span className="text-sm font-bold tracking-tight">{label}</span>
        </div>
        {badge && (
            <span className="h-5 w-5 rounded-full bg-red-600 text-[10px] font-bold text-white flex items-center justify-center border-2 border-[#020617]">{badge}</span>
        )}
    </Link>
)
