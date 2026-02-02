import React from 'react'
import { Sidebar } from './Sidebar'

interface DashboardLayoutProps {
    children: React.ReactNode
}

/**
 * DashboardLayout Component (Local Scope: Navigation)
 * Main shell for all authenticated pages.
 */
export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
    return (
        <div className="flex min-h-screen bg-gray-50 dark:bg-gray-900">
            {/* Sidebar - Persistent on Desktop */}
            <Sidebar />

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto p-8">
                <div className="mx-auto max-w-7xl">
                    {children}
                </div>
            </main>
        </div>
    )
}
