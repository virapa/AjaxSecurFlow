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
        render(<VoucherForm onSuccess={async () => { }} />)

        expect(screen.getByLabelText(/canjear código/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /canjear y aplicar/i })).toBeInTheDocument()
    })

    it('should call billingService.redeemVoucher when form is submitted', async () => {
        const redeemMock = vi.mocked(billingService.redeemVoucher).mockResolvedValue({ status: 'success', message: 'OK' })
        render(<VoucherForm onSuccess={async () => { }} />)

        const input = screen.getByLabelText(/canjear código/i)
        fireEvent.change(input, { target: { value: 'AJAX-1234-5678' } })

        fireEvent.click(screen.getByRole('button', { name: /canjear y aplicar/i }))

        await waitFor(() => {
            expect(redeemMock).toHaveBeenCalledWith('AJAX-1234-5678')
        })
    })

    it('should display success message on successful redemption', async () => {
        vi.mocked(billingService.redeemVoucher).mockResolvedValue({ status: 'success', message: 'OK' })
        render(<VoucherForm onSuccess={async () => { }} />)

        fireEvent.change(screen.getByLabelText(/canjear código/i), { target: { value: 'AJAX-VALID' } })
        fireEvent.click(screen.getByRole('button', { name: /canjear y aplicar/i }))

        expect(await screen.findByText(/código validado/i)).toBeInTheDocument()
    })

    it('should display error message on failed redemption', async () => {
        vi.mocked(billingService.redeemVoucher).mockRejectedValue(new Error('Código inválido'))
        render(<VoucherForm onSuccess={async () => { }} />)

        fireEvent.change(screen.getByLabelText(/canjear código/i), { target: { value: 'AJAX-INVALID' } })
        fireEvent.click(screen.getByRole('button', { name: /canjear y aplicar/i }))

        expect(await screen.findByText(/código inválido/i)).toBeInTheDocument()
    })
})
