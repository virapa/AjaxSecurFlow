import React, { useState } from 'react'
import { Input } from '@/shared/components/Input'
import { Button } from '@/shared/components/Button'
import { billingService } from './billing.service'

/**
 * VoucherForm Component (Local Scope: Billing)
 * Allows users to redeem activation codes.
 */
export const VoucherForm: React.FC = () => {
    const [code, setCode] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setStatus(null)

        try {
            await billingService.redeemVoucher(code)
            setStatus({ type: 'success', message: 'Código canjeado con éxito. Tu suscripción se ha actualizado.' })
            setCode('')
        } catch (err: any) {
            setStatus({
                type: 'error',
                message: err.message || 'Error al canjear el código. Verifica que sea correcto.'
            })
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <Input
                label="Código de Activación"
                placeholder="AJAX-XXXX-XXXX"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                required
                disabled={isLoading}
            />
            {status && (
                <p className={`text-sm font-medium ${status.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {status.message}
                </p>
            )}
            <Button
                type="submit"
                className="w-full"
                disabled={isLoading || !code.trim()}
            >
                {isLoading ? 'Procesando...' : 'Canjear Código'}
            </Button>
        </form>
    )
}
