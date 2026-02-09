import { NextRequest, NextResponse } from 'next/server'
import { describe, it, expect, vi, Mock } from 'vitest'
import middleware from './proxy'

// Mock NextURL to avoid internal issues
vi.mock('next/server', async () => {
    const actual = await vi.importActual('next/server')
    return {
        ...actual as any,
        NextResponse: class {
            static redirect = vi.fn((url) => ({ url, redirected: true }))
            static next = vi.fn(() => ({ next: true }))
            status: number
            constructor(body: unknown, init: { status?: number }) {
                this.status = init?.status || 200
            }
        },
    }
})

describe('Auth Middleware', () => {
    it('should redirect unauthenticated users to /login when accessing dashboard', () => {
        const req = {
            nextUrl: { pathname: '/dashboard' },
            cookies: {
                get: vi.fn().mockReturnValue(undefined), // No token
            },
            url: 'http://localhost:3000/dashboard',
        } as unknown as NextRequest

        middleware(req)

        expect(NextResponse.redirect).toHaveBeenCalledWith(
            expect.objectContaining({ pathname: '/login' })
        )
    })

    it('should allow authenticated users to access dashboard', () => {
        const req = {
            nextUrl: { pathname: '/dashboard' },
            cookies: {
                get: vi.fn().mockReturnValue({ value: 'valid-token' }),
            },
            url: 'http://localhost:3000/dashboard',
        } as unknown as NextRequest

        middleware(req)

        expect(NextResponse.next).toHaveBeenCalled()
    })

    it('should redirect authenticated users away from /login', () => {
        const req = {
            nextUrl: { pathname: '/login' },
            cookies: {
                get: vi.fn().mockReturnValue({ value: 'valid-token' }),
            },
            url: 'http://localhost:3000/login',
        } as unknown as NextRequest

        middleware(req)

        expect(NextResponse.redirect).toHaveBeenCalledWith(
            expect.objectContaining({ pathname: '/dashboard' })
        )
    })

    describe('Request Shield', () => {
        it('should block malicious script extensions (.php)', () => {
            const req = {
                nextUrl: { pathname: '/admin.php' },
                headers: { get: vi.fn().mockReturnValue(null) },
            } as unknown as NextRequest

            const res = middleware(req) as { status: number }

            expect(res.status).toBe(403)
        })

        it('should block sensitive file access (.env)', () => {
            const req = {
                nextUrl: { pathname: '/config/.env' },
                headers: { get: vi.fn().mockReturnValue(null) },
            } as unknown as NextRequest

            const res = middleware(req) as { status: number }

            expect(res.status).toBe(403)
        })

        it('should block path traversal attempts (../)', () => {
            const req = {
                nextUrl: { pathname: '/static/../../etc/passwd' },
                headers: { get: vi.fn().mockReturnValue(null) },
            } as unknown as NextRequest

            const res = middleware(req) as { status: number }

            expect(res.status).toBe(403)
        })

        it('should allow normal static-like paths that are not malicious', () => {
            const req = {
                nextUrl: { pathname: '/dashboard/settings' },
                cookies: { get: vi.fn().mockReturnValue({ value: 'token' }) },
                url: 'http://localhost:3000/dashboard/settings',
            } as unknown as NextRequest

            middleware(req)
            expect(NextResponse.next).toHaveBeenCalled()
        })
    })
})
