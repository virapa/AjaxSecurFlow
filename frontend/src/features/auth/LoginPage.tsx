'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { Card } from '@/shared/components/Card'
import { Input } from '@/shared/components/Input'
import { Button } from '@/shared/components/Button'
import { authService } from './auth.service'
import { es as t } from '@/shared/i18n/es'

/**
 * LoginPage Component (Local Scope: Auth)
 * Premium Industrial design for authentication with i18n support.
 */
const LoginPage: React.FC = () => {
    const router = useRouter()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError(null)

        try {
            await authService.login(email, password)
            router.push('/dashboard')
        } catch (err: unknown) {
            const error = err as Error
            setError(error.message || `${t.auth.errorTitle}. ${t.auth.errorDetail}`)
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="relative flex min-h-screen items-center justify-center bg-[#020617] p-4 selection:bg-blue-500/30 overflow-hidden">
            {/* Background Decorative Gradients */}
            <div className="absolute top-[-20%] left-[-10%] h-[600px] w-[600px] rounded-full bg-blue-600/10 blur-[120px]" />
            <div className="absolute bottom-[-20%] right-[-10%] h-[600px] w-[600px] rounded-full bg-blue-600/5 blur-[120px]" />

            <div className="z-10 w-full max-w-md">
                {/* Brand Header */}
                <div className="mb-10 text-center">
                    <Link href="/" className="inline-flex items-center gap-2 group transition-all">
                        <div className="h-10 w-10 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
                            A
                        </div>
                        <span className="text-2xl font-bold tracking-tight text-white">AjaxSecurFlow</span>
                    </Link>
                </div>

                <Card
                    className="border-white/5 bg-white/[0.02] backdrop-blur-xl shadow-2xl relative overflow-hidden"
                    header={
                        <div className="text-center space-y-4 pt-4">
                            <div className="flex justify-center flex-col items-center gap-4">
                                <Image
                                    src="/images/ajax-logo-login.png"
                                    alt="AJAX Systems"
                                    width={100}
                                    height={32}
                                    className="h-8 w-auto object-contain brightness-200"
                                />
                                <div className="h-px w-12 bg-blue-500/50" />
                                <h1 className="text-lg font-bold text-white tracking-wide uppercase">
                                    {t.auth.title}
                                </h1>
                            </div>
                        </div>
                    }
                >
                    <form className="space-y-6" onSubmit={handleSubmit}>
                        <div className="space-y-4">
                            <Input
                                label={t.auth.emailLabel}
                                type="email"
                                placeholder="tuemail@ejemplo.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={isLoading}
                                className="bg-white/[0.03] border-white/10 text-white placeholder:text-gray-600 focus:border-blue-500/50"
                            />
                            <Input
                                label={t.auth.passwordLabel}
                                type="password"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                disabled={isLoading}
                                className="bg-white/[0.03] border-white/10 text-white placeholder:text-gray-600 focus:border-blue-500/50"
                            />
                        </div>

                        {error && (
                            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 text-center animate-in fade-in zoom-in duration-300">
                                {error}
                            </div>
                        )}

                        <div className="space-y-6">
                            <Button
                                type="submit"
                                className="w-full h-12 font-bold shadow-lg shadow-blue-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <span className="flex items-center gap-2 justify-center">
                                        <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        {t.auth.loggingIn}
                                    </span>
                                ) : (
                                    t.auth.loginButton
                                )}
                            </Button>

                            <div className="mx-auto max-w-[320px] rounded-lg bg-blue-500/5 border border-blue-500/10 p-3">
                                <p className="text-[11px] leading-relaxed text-blue-400 font-medium text-center">
                                    {t.auth.instruction}
                                </p>
                            </div>
                        </div>
                    </form>
                </Card>

                <div className="mt-12 flex justify-center gap-6 text-[10px] uppercase tracking-widest font-semibold text-gray-600">
                    <span>Industrial Security</span>
                    <span>•</span>
                    <span>GDPR Compliant</span>
                    <span>•</span>
                    <span>Ajax Partner</span>
                </div>
            </div>
        </div>
    )
}

export default LoginPage
