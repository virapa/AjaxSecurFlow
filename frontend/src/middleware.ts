import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Middleware: Global Route Protection
 * This runs on every request to provide edge-level security.
 */
export default function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl

    // We check for the access_token cookie
    // Note: Since it's HTTPOnly, we can only check its presence here, not its value/content
    const accessToken = request.cookies.get('access_token')

    const isPublicRoute = pathname === '/login' || pathname === '/'
    const isDashboardRoute = pathname.startsWith('/dashboard')

    // Case 1: Unauthenticated user trying to access the dashboard
    if (!accessToken && isDashboardRoute) {
        const loginUrl = new URL('/login', request.url)
        return NextResponse.redirect(loginUrl)
    }

    // Case 2: Authenticated user trying to access the login page
    if (accessToken && pathname === '/login') {
        const dashboardUrl = new URL('/dashboard', request.url)
        return NextResponse.redirect(dashboardUrl)
    }

    return NextResponse.next()
}

/**
 * Configure which routes this middleware should run on.
 */
export const config = {
    matcher: [
        '/dashboard/:path*',
        '/login',
    ],
}
