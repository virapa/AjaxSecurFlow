import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const MALICIOUS_PATTERNS = [
    // Legacy server extensions (PHP, ASP, JSP, etc)
    /\.(php|asp|aspx|jsp|cgi|pl|cfm|rb|py)$/i,
    // Sensitive files and directories
    /(\.env|\.git|\.vscode|\.ssh|web\.config|composer\.json|package\.json|Dockerfile)/i,
    // Common admin panels and backdoors
    /\/(admin|phpmyadmin|wp-admin|wp-content|wordpress|administrator|backoffice|cp|controlpanel|manager)/i,
    // System files and path traversal
    /(\/etc\/passwd|\/etc\/shadow|\/windows\/system\.ini|win\.ini|\.\.\/)/i,
    // Database and log dumps
    /\.(sql|bak|old|swp|log|sqlite|db)$/i,
    // Specific probes from the log
    /\/(sdk|jk-status|balancer-manager|admin-console|webmail|happyaxis|uddiclient|fckeditor)/i
]

/**
 * Middleware: Global Route Protection & Request Shield
 * This runs on every request to provide edge-level security.
 */
export default function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl

    // 1. Request Shield: Block malicious probes
    // We check the pathname against known exploit patterns
    const isMalicious = MALICIOUS_PATTERNS.some(pattern => pattern.test(pathname))

    if (isMalicious) {
        const ip = request.headers.get('x-forwarded-for') || 'unknown'
        console.warn(`[SECURITY] Blocked malicious probe: ${pathname} from ${ip}`)
        return new NextResponse(null, {
            status: 403,
            statusText: 'Forbidden'
        })
    }

    // 2. Authentication Flow
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
        /*
         * Match all request paths except for the ones starting with:
         * - api (API routes)
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         */
        '/((?!api|_next/static|_next/image|favicon.ico).*)',
    ],
}
