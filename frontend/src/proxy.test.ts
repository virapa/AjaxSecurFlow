import { NextRequest, NextResponse } from 'next/server'
import { describe, it, expect, vi } from 'vitest'
import middleware from './proxy'

// Mock NextURL to avoid internal issues
vi.mock('next/server', async () => {
    const actual = await vi.importActual('next/server')
    return {
        ...actual as any,
        NextResponse: {
            redirect: vi.fn((url) => ({ url, redirected: true })),
            next: vi.fn(() => ({ next: true })),
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
})
