'use client'

import React, { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { es as t } from '@/shared/i18n/es'
import { authService } from '@/features/auth/auth.service'

interface DashboardHeaderProps {
    title?: string
    user?: any
    unreadNotificationsCount?: number
    searchQuery?: string
    setSearchQuery?: (query: string) => void
    isRefreshing?: boolean
    onRefresh?: () => void
    activeHubsCount?: number
    totalHubsCount?: number
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({
    title,
    user,
    unreadNotificationsCount = 0,
    searchQuery,
    setSearchQuery,
    isRefreshing,
    onRefresh,
    activeHubsCount,
    totalHubsCount
}) => {
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
    const menuRef = useRef<HTMLDivElement>(null)

    // Click outside handler for user menu
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsUserMenuOpen(false)
            }
        }
        document.addEventListener('click', handleClickOutside)
        return () => {
            document.removeEventListener('click', handleClickOutside)
        }
    }, [])

    const handleLogout = async (e?: React.MouseEvent) => {
        if (e) {
            e.preventDefault()
            e.stopPropagation()
        }

        localStorage.removeItem('ajax_access_token')
        document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT'

        try {
            await authService.logout()
        } catch (err) {
            console.warn('Network logout failed, proceeding with local cleanup:', err)
        } finally {
            window.location.href = '/'
        }
    }

    return (
        <header className="h-20 border-b border-white/5 px-10 flex items-center justify-between sticky top-0 z-30 bg-[#020617]/80 backdrop-blur-xl">
            <div className="flex items-center gap-8">
                <h2 className="text-lg font-bold tracking-tight">{title || t.dashboard.title}</h2>

                {setSearchQuery && (
                    <div className="relative group hidden md:block">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-sm">🔍</span>
                        <input
                            type="text"
                            placeholder={t.dashboard.searchPlaceholder}
                            value={searchQuery || ''}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="bg-white/5 border border-white/10 rounded-xl pl-12 pr-10 py-2.5 text-xs w-[320px] focus:outline-none focus:border-cyan-500/50 transition-all placeholder:text-gray-600"
                        />
                        {searchQuery && (
                            <button
                                onClick={() => setSearchQuery('')}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors text-xs"
                            >
                                ✕
                            </button>
                        )}
                    </div>
                )}
            </div>

            <div className="flex items-center gap-6">
                {/* System Status - Only show if hub counts are provided */}
                {typeof activeHubsCount === 'number' && typeof totalHubsCount === 'number' && (
                    <div className="px-4 py-1.5 rounded-full bg-white/5 border border-white/10 flex items-center gap-2">
                        {(() => {
                            const allOnline = activeHubsCount === totalHubsCount && totalHubsCount > 0;

                            if (allOnline) {
                                return (
                                    <>
                                        <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
                                        <span className="text-[10px] font-bold uppercase tracking-widest text-green-400">
                                            {t.dashboard.systemStatus.secure}
                                        </span>
                                    </>
                                );
                            } else {
                                return (
                                    <>
                                        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                                        <span className="text-[10px] font-bold uppercase tracking-widest text-red-500">
                                            {t.dashboard.systemStatus.attention}
                                        </span>
                                    </>
                                );
                            }
                        })()}
                    </div>
                )}

                {/* Refresh Button - Only show if onRefresh provided */}
                {onRefresh && (
                    <button
                        onClick={onRefresh}
                        disabled={isRefreshing}
                        className={`text-gray-500 hover:text-white transition-all transform active:scale-95 ${isRefreshing ? 'opacity-50' : ''}`}
                        title={t.dashboard.nav.dashboard}
                    >
                        <span className={`inline-block ${isRefreshing ? 'animate-spin' : ''}`}>🔄</span>
                    </button>
                )}

                {(typeof activeHubsCount === 'number' || onRefresh) && (
                    <div className="h-10 w-[1px] bg-white/10 mx-2" />
                )}

                {/* User Profile with Dropdown */}
                <div className="flex items-center gap-3 relative" ref={menuRef}>
                    <button
                        onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                        className="flex items-center gap-3 hover:bg-white/5 p-2 rounded-2xl transition-all"
                    >
                        <div className="text-right hidden sm:block">
                            <div className="flex items-center gap-2">
                                <p className="text-xs font-bold text-white">
                                    {user?.ajax_info?.firstName || user?.email || t.dashboard.profile.adminUser}
                                </p>
                                <Link href="/notifications" className="relative hover:scale-110 transition-transform block">
                                    <span className="text-sm">🔔</span>
                                    {unreadNotificationsCount > 0 && (
                                        <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-red-600 border border-[#020617] flex items-center justify-center text-[7px] font-bold text-white">
                                            {unreadNotificationsCount}
                                        </span>
                                    )}
                                </Link>
                            </div>
                            <p className="text-[9px] font-medium text-gray-500 text-left">
                                {user?.ajax_info?.login || t.dashboard.profile.role}
                            </p>
                        </div>
                        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 border border-white/10 flex items-center justify-center text-xs shadow-lg overflow-hidden">
                            {user?.ajax_info?.imageUrls?.small ? (
                                <Image
                                    src={user.ajax_info.imageUrls.small}
                                    alt="Profile"
                                    width={40}
                                    height={40}
                                    className="w-full h-full object-cover"
                                    onError={(e) => {
                                        const target = e.target as HTMLImageElement;
                                        target.style.display = 'none';
                                        if (target.parentElement) {
                                            target.parentElement.textContent = '👤';
                                        }
                                    }}
                                />
                            ) : (
                                '👤'
                            )}
                        </div>
                    </button>

                    {/* Dropdown Menu */}
                    {isUserMenuOpen && (
                        <div className="absolute right-0 top-full mt-2 w-48 bg-[#0f172a] border border-white/10 rounded-2xl shadow-2xl z-50 py-2 overflow-hidden animate-in fade-in zoom-in duration-200">
                            <Link href="/profile" className="flex items-center gap-2 px-4 py-3 text-xs font-bold text-gray-400 hover:text-white hover:bg-white/5 transition-colors">
                                <span>⚙️</span> {t.dashboard.nav.settings}
                            </Link>
                            <div className="h-px bg-white/5 my-1" />
                            <button
                                onMouseDown={(e) => {
                                    e.stopPropagation()
                                    handleLogout(e as any)
                                }}
                                className="w-full h-full flex items-center gap-2 px-4 py-3 text-xs font-bold text-red-100 bg-red-500/10 hover:bg-red-500/20 transition-all text-left z-[60]"
                            >
                                <span>🚪</span> {t.dashboard.nav.logout}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </header>
    )
}
