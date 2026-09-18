import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ApiTokensSection } from './ApiTokensSection'
import { apiTokenService } from './api-token.service'
import { es as t } from '@/shared/i18n/es'

vi.mock('./api-token.service', () => ({
    apiTokenService: { list: vi.fn(), create: vi.fn(), revoke: vi.fn() }
}))

const i18n = t.dashboard.profilePage.integrations
const existing = { id: 1, name: 'HA Casa', prefix: 'asf_abcdefgh', created_at: '2026-09-18T10:00:00Z', last_used_at: null }

describe('ApiTokensSection (Local Scope: Integrations)', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        vi.mocked(apiTokenService.list).mockResolvedValue([existing])
    })

    it('lists active tokens with prefix, never the raw token', async () => {
        render(<ApiTokensSection plan="pro" />)
        await waitFor(() => expect(screen.getByText('HA Casa')).toBeInTheDocument())
        expect(screen.getByText('asf_abcdefgh')).toBeInTheDocument()
        expect(screen.getByText(i18n.never)).toBeInTheDocument()
    })

    it('creates a token and shows the raw value once', async () => {
        vi.mocked(apiTokenService.create).mockResolvedValue({ ...existing, id: 2, name: 'Nuevo', token: 'asf_abcdefghRAWVALUE' })
        render(<ApiTokensSection plan="pro" />)
        await waitFor(() => expect(apiTokenService.list).toHaveBeenCalled())

        fireEvent.click(screen.getByText(i18n.createButton))
        fireEvent.change(screen.getByPlaceholderText(i18n.namePlaceholder), { target: { value: 'Nuevo' } })
        fireEvent.click(screen.getByText(i18n.confirmCreate))

        await waitFor(() => expect(screen.getByTestId('raw-token')).toHaveTextContent('asf_abcdefghRAWVALUE'))
        expect(apiTokenService.create).toHaveBeenCalledWith('Nuevo')
        expect(screen.getByText(i18n.createdWarning)).toBeInTheDocument()

        fireEvent.click(screen.getByText(i18n.done))
        await waitFor(() => expect(screen.queryByTestId('raw-token')).not.toBeInTheDocument())
        expect(apiTokenService.list).toHaveBeenCalledTimes(2)
    })

    it('revokes after confirmation', async () => {
        vi.mocked(apiTokenService.revoke).mockResolvedValue(undefined)
        render(<ApiTokensSection plan="pro" />)
        await waitFor(() => expect(screen.getByText('HA Casa')).toBeInTheDocument())

        fireEvent.click(screen.getByText(i18n.revoke))
        expect(screen.getByText(i18n.revokeConfirm)).toBeInTheDocument()
        fireEvent.click(screen.getByTestId('confirm-revoke'))

        await waitFor(() => expect(apiTokenService.revoke).toHaveBeenCalledWith(1))
        expect(apiTokenService.list).toHaveBeenCalledTimes(2)
    })

    it('disables creation for the free plan', async () => {
        render(<ApiTokensSection plan="free" />)
        expect(screen.getByText(i18n.planRequired)).toBeInTheDocument()
        expect(screen.getByText(i18n.createButton)).toBeDisabled()
        expect(apiTokenService.list).not.toHaveBeenCalled()
    })

    it('shows the limit message on a 400 from the backend', async () => {
        vi.mocked(apiTokenService.create).mockRejectedValue(new Error('API Error: 400 Maximum of 10 active tokens reached'))
        render(<ApiTokensSection plan="pro" />)
        await waitFor(() => expect(apiTokenService.list).toHaveBeenCalled())
        fireEvent.click(screen.getByText(i18n.createButton))
        fireEvent.change(screen.getByPlaceholderText(i18n.namePlaceholder), { target: { value: 'X' } })
        fireEvent.click(screen.getByText(i18n.confirmCreate))
        await waitFor(() => expect(screen.getByText(i18n.limitReached)).toBeInTheDocument())
    })
})
