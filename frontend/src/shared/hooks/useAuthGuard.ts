'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

/**
 * useAuthGuard Hook
 * 
 * Client-side authentication guard for protected components.
 * Checks for authentication token and redirects to login if not found.
 * 
 * This provides a second layer of defense and improves UX by:
 * - Preventing flash of protected content
 * - Showing loading state during auth check
 * - Handling client-side navigation scenarios
 * 
 * Usage:
 * ```tsx
 * const { isAuthenticated, isLoading } = useAuthGuard()
 * if (isLoading) return <LoadingSpinner />
 * if (!isAuthenticated) return null // Will redirect
 * ```
 */
export function useAuthGuard() {
    const router = useRouter()
    const [isAuthenticated, setIsAuthenticated] = useState(false)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        // Only run on client side
        if (typeof window === 'undefined') {
            return
        }

        // Check for token in localStorage (primary) or cookies (fallback)
        const checkAuth = () => {
            try {
                // Check localStorage first
                const token = localStorage.getItem('ajax_access_token')

                // Check cookies as fallback
                const cookieToken = document.cookie
                    .split('; ')
                    .find(row => row.startsWith('access_token='))
                    ?.split('=')[1]

                if (token || cookieToken) {
                    setIsAuthenticated(true)
                    setIsLoading(false)
                } else {
                    // No token found, redirect to login
                    setIsAuthenticated(false)
                    setIsLoading(false)
                    const currentPath = window.location.pathname
                    router.push(`/login?redirect=${encodeURIComponent(currentPath)}`)
                }
            } catch (error) {
                console.error('[AuthGuard] Error checking authentication:', error)
                setIsAuthenticated(false)
                setIsLoading(false)
                router.push('/login')
            }
        }

        checkAuth()
    }, [router])

    return { isAuthenticated, isLoading }
}
