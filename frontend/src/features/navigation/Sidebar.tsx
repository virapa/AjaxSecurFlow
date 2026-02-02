import React from 'react'
import Link from 'next/link'
import { Button } from '@/shared/components/Button'

/**
 * Sidebar Component (Local Scope: Navigation)
 * Primary navigation for the authenticated dashboard.
 */
export const Sidebar: React.FC = () => {
    const navItems = [
        { name: 'Panel', href: '/dashboard' },
        { name: 'Hubs', href: '/dashboard/hubs' },
        { name: 'Facturación', href: '/dashboard/billing' },
        { name: 'Notificaciones', href: '/dashboard/notifications' },
    ]

    return (
        <nav className="flex h-screen w-64 flex-col border-r bg-white p-4 dark:border-gray-800 dark:bg-gray-950">
            <div className="mb-8 px-2 py-4">
                <h1 className="text-xl font-bold tracking-tight text-blue-600 dark:text-blue-400">
                    AjaxSecurFlow
                </h1>
            </div>

            <div className="flex-1 space-y-1">
                {navItems.map((item) => (
                    <Link
                        key={item.href}
                        href={item.href}
                        className="group flex items-center rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white transition-colors"
                    >
                        {item.name}
                    </Link>
                ))}
            </div>

            <div className="mt-auto border-t pt-4 dark:border-gray-800">
                <Button variant="ghost" className="w-full justify-start text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20">
                    Salir
                </Button>
            </div>
        </nav>
    )
}
