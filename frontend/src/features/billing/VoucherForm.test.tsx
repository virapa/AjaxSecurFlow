import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { VoucherForm } from './VoucherForm'
import { billingService } from './billing.service'

// Mock the local billing service
vi.mock('./billing.service', () => ({
    billingService: {
        redeemVoucher: vi.fn()
    }
}))

describe('VoucherForm Component (Local Scope: Billing)', () => {
    it('should render the voucher input and submit button', () => {
        render(<VoucherForm />)

        expect(screen.getByLabelText(/código de activación/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /canjear código/i })).toBeInTheDocument()
    })

    it('should call billingService.redeemVoucher when form is submitted', async () => {
        const redeemMock = vi.mocked(billingService.redeemVoucher).mockResolvedValue({ status: 'success' })
        render(<VoucherForm />)

        const input = screen.getByLabelText(/código de activación/i)
        fireEvent.change(input, { target: { value: 'AJAX-1234-5678' } })

        fireEvent.click(screen.getByRole('button', { name: /canjear código/i }))

        await waitFor(() => {
            expect(redeemMock).toHaveBeenCalledWith('AJAX-1234-5678')
        })
    })

    it('should display success message on successful redemption', async () => {
        vi.mocked(billingService.redeemVoucher).mockResolvedValue({ status: 'success' })
        render(<VoucherForm />)

        fireEvent.change(screen.getByLabelText(/código de activación/i), { target: { value: 'AJAX-VALID' } })
        fireEvent.click(screen.getByRole('button', { name: /canjear código/i }))

        expect(await screen.findByText(/código canjeado con éxito/i)).toBeInTheDocument()
    })

    it('should display error message on failed redemption', async () => {
        vi.mocked(billingService.redeemVoucher).mockRejectedValue(new Error('Código inválido'))
        render(<VoucherForm />)

        fireEvent.change(screen.getByLabelText(/código de activación/i), { target: { value: 'AJAX-INVALID' } })
        fireEvent.click(screen.getByRole('button', { name: /canjear código/i }))

        expect(await screen.findByText(/código inválido/i)).toBeInTheDocument()
    })
})
