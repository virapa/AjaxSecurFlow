'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { es as t } from '@/shared/i18n/es'
import { apiTokenService, ApiToken, ApiTokenCreated } from './api-token.service'

const i18n = t.dashboard.profilePage.integrations
const HA_DOCS_URL = 'https://github.com/virapa/ajaxsecurflow-hass#readme'
const PLANS_WITH_TOKENS = ['basic', 'pro', 'premium']

interface ApiTokensSectionProps {
    plan?: string
    active?: boolean
}

const formatDate = (iso?: string | null) =>
    iso ? new Date(iso).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' }) : i18n.never

/**
 * Integration Tokens Section (Local Scope: features/integrations)
 * Lists, creates and revokes long-lived API tokens. The raw token is shown once, right after creation.
 */
export const ApiTokensSection: React.FC<ApiTokensSectionProps> = ({ plan, active }) => {
    const allowed = active === true && PLANS_WITH_TOKENS.includes(plan || '')
    const [tokens, setTokens] = useState<ApiToken[]>([])
    const [isCreating, setIsCreating] = useState(false)
    const [newName, setNewName] = useState('')
    const [created, setCreated] = useState<ApiTokenCreated | null>(null)
    const [copied, setCopied] = useState(false)
    const [pendingRevoke, setPendingRevoke] = useState<number | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [busy, setBusy] = useState(false)

    const load = useCallback(async () => {
        try {
            setTokens(await apiTokenService.list())
            setError(null)
        } catch {
            setError(i18n.error)
        }
    }, [])

    useEffect(() => {
        if (allowed) load()
    }, [allowed, load])

    const handleCreate = async () => {
        if (!newName.trim()) return
        setBusy(true)
        setError(null)
        try {
            const result = await apiTokenService.create(newName.trim())
            setCreated(result)
            setIsCreating(false)
            setNewName('')
        } catch (err) {
            const status = (err as { status?: number }).status
            setError(status === 400 ? i18n.limitReached : status === 403 ? i18n.planRequired : i18n.error)
        } finally {
            setBusy(false)
        }
    }

    const handleDone = async () => {
        setCreated(null)
        setCopied(false)
        await load()
    }

    const handleCopy = async () => {
        if (!created) return
        try {
            await navigator.clipboard.writeText(created.token)
            setCopied(true)
        } catch {
            setCopied(false)
        }
    }

    const handleRevoke = async (id: number) => {
        setBusy(true)
        setError(null)
        try {
            await apiTokenService.revoke(id)
            setPendingRevoke(null)
            await load()
        } catch (err) {
            const status = (err as { status?: number }).status
            setError(status === 403 ? i18n.planRequired : i18n.error)
        } finally {
            setBusy(false)
        }
    }

    return (
        <section className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-8 space-y-6" data-testid="api-tokens-section">
            <div className="space-y-2">
                <h3 className="text-sm font-black uppercase tracking-widest text-white">{i18n.title}</h3>
                <p className="text-[10px] text-gray-500 leading-tight">{i18n.description}</p>
                <a href={HA_DOCS_URL} target="_blank" rel="noreferrer" className="inline-block text-xs font-bold text-cyan-400 hover:text-cyan-300">
                    {i18n.docsLink} &rarr;
                </a>
            </div>

            {!allowed && (
                <div className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-xs font-bold text-center">
                    {i18n.planRequired}
                </div>
            )}

            {error && (
                <div role="alert" className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-bold text-center">
                    {error}
                </div>
            )}

            {created && (
                <div aria-live="polite" className="p-5 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 space-y-3">
                    <p className="text-xs font-black uppercase tracking-widest text-cyan-400">{i18n.createdTitle}</p>
                    <p className="text-[10px] text-gray-400">{i18n.createdWarning}</p>
                    <code data-testid="raw-token" className="block w-full break-all bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-xs font-mono text-cyan-300">
                        {created.token}
                    </code>
                    <div className="flex gap-3">
                        <button onClick={handleCopy} className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-[10px] font-black uppercase tracking-widest text-white">
                            {copied ? i18n.copied : i18n.copy}
                        </button>
                        <button onClick={handleDone} className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-[10px] font-black uppercase tracking-widest text-white">
                            {i18n.done}
                        </button>
                    </div>
                </div>
            )}

            {allowed && !created && (
                isCreating ? (
                    <div className="flex flex-col md:flex-row gap-3">
                        <input
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            placeholder={i18n.namePlaceholder}
                            aria-label={i18n.namePlaceholder}
                            maxLength={64}
                            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white font-medium outline-none focus:border-cyan-500/50"
                        />
                        <button onClick={handleCreate} disabled={busy || !newName.trim()} className="px-5 py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-[10px] font-black uppercase tracking-widest text-white">
                            {i18n.confirmCreate}
                        </button>
                        <button onClick={() => { setIsCreating(false); setNewName('') }} className="px-5 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-[10px] font-black uppercase tracking-widest text-white">
                            {i18n.cancel}
                        </button>
                    </div>
                ) : (
                    <button onClick={() => setIsCreating(true)} className="w-full py-4 rounded-2xl bg-cyan-600 hover:bg-cyan-500 text-sm font-black uppercase tracking-widest text-white transition-all shadow-xl shadow-cyan-500/20 active:scale-[0.98]">
                        {i18n.createButton}
                    </button>
                )
            )}

            {!allowed && (
                <button disabled className="w-full py-4 rounded-2xl bg-cyan-600 opacity-40 cursor-not-allowed text-sm font-black uppercase tracking-widest text-white">
                    {i18n.createButton}
                </button>
            )}

            {allowed && (
                <div className="overflow-x-auto">
                    {tokens.length === 0 ? (
                        <p className="text-xs text-gray-500 text-center py-4">{i18n.empty}</p>
                    ) : (
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-white/5">
                                    <th className="py-3 pr-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{i18n.columns.name}</th>
                                    <th className="py-3 pr-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{i18n.columns.prefix}</th>
                                    <th className="py-3 pr-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{i18n.columns.created}</th>
                                    <th className="py-3 pr-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{i18n.columns.lastUsed}</th>
                                    <th className="py-3"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {tokens.map((token) => (
                                    <tr key={token.id} className="border-b border-white/5 last:border-0">
                                        <td className="py-3 pr-4 text-sm font-bold text-white">{token.name}</td>
                                        <td className="py-3 pr-4"><code className="px-2 py-1 rounded-lg bg-white/5 text-xs font-mono text-cyan-300">{`${token.prefix}…`}</code></td>
                                        <td className="py-3 pr-4 text-xs text-gray-400">{formatDate(token.created_at)}</td>
                                        <td className="py-3 pr-4 text-xs text-gray-400">{formatDate(token.last_used_at)}</td>
                                        <td className="py-3 text-right">
                                            {pendingRevoke === token.id ? (
                                                <div className="flex flex-col items-end gap-2">
                                                    <span className="text-[10px] text-red-400">{i18n.revokeConfirm}</span>
                                                    <div className="flex gap-2">
                                                        <button data-testid="confirm-revoke" onClick={() => handleRevoke(token.id)} disabled={busy} className="px-3 py-1.5 rounded-lg bg-red-500/20 text-red-400 text-[10px] font-black uppercase tracking-widest">
                                                            {i18n.revoke}
                                                        </button>
                                                        <button onClick={() => setPendingRevoke(null)} className="px-3 py-1.5 rounded-lg bg-white/5 text-white text-[10px] font-black uppercase tracking-widest">
                                                            {i18n.cancel}
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <button onClick={() => setPendingRevoke(token.id)} className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-[10px] font-black uppercase tracking-widest">
                                                    {i18n.revoke}
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            )}
        </section>
    )
}
