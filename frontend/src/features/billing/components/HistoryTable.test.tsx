import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { HistoryTable } from './BillingSubComponents'
import { BillingHistoryItem } from '../types'

describe('HistoryTable Component', () => {
    const mockHistory: BillingHistoryItem[] = [
        {
            id: 'inv_1',
            date: '2023-10-12T10:00:00Z',
            type: 'payment',
            description: 'Premium Subscription',
            amount: '29.99 USD',
            status: 'Pagado',
            download_url: 'http://stripe.com/pdf'
        },
        {
            id: 'vouch_1',
            date: '2023-09-10T15:00:00Z',
            type: 'voucher',
            description: 'Voucher Redemption',
            amount: '30 Días',
            status: 'Aplicado'
        }
    ]

    it('renders history items correctly', () => {
        render(<HistoryTable history={mockHistory} />)

        expect(screen.getByText('Premium Subscription')).toBeInTheDocument()
        expect(screen.getByText('Voucher Redemption')).toBeInTheDocument()
        expect(screen.getByText('29.99 USD')).toBeInTheDocument()
        expect(screen.getByText('30 Días')).toBeInTheDocument()
    })

    it('renders download link ONLY for payments with download_url', () => {
        render(<HistoryTable history={mockHistory} />)

        const downloadLinks = screen.getAllByRole('link', { name: /descargar/i })
        expect(downloadLinks).toHaveLength(1)
        expect(downloadLinks[0]).toHaveAttribute('href', 'http://stripe.com/pdf')
    })

    it('renders empty state when no history is provided', () => {
        render(<HistoryTable history={[]} />)
        expect(screen.getByText(/no hay registros/i)).toBeInTheDocument()
    })

    it('formats dates correctly in es-ES', () => {
        render(<HistoryTable history={mockHistory} />)
        // Oct -> oct. (or similar depending on environment, but should contain 'oct' and '12')
        expect(screen.getByText(/12/)).toBeInTheDocument()
        expect(screen.getByText(/oct/i)).toBeInTheDocument()
    })
})
