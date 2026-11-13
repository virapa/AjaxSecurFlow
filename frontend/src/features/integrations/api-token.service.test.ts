import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from '@/infrastructure/api-client'
import { apiTokenService } from './api-token.service'

vi.mock('@/infrastructure/api-client', () => ({
    apiClient: { get: vi.fn(), post: vi.fn(), delete: vi.fn() }
}))

describe('apiTokenService', () => {
    beforeEach(() => vi.clearAllMocks())

    it('lists tokens from /auth/api-tokens', async () => {
        vi.mocked(apiClient.get).mockResolvedValue([{ id: 1, name: 'HA', prefix: 'asf_abcdefgh', created_at: '2026-09-18T00:00:00Z' }])
        const tokens = await apiTokenService.list()
        expect(apiClient.get).toHaveBeenCalledWith('/auth/api-tokens')
        expect(tokens[0].prefix).toBe('asf_abcdefgh')
    })

    it('creates a token with a name', async () => {
        vi.mocked(apiClient.post).mockResolvedValue({ id: 2, name: 'HA', prefix: 'asf_abcdefgh', token: 'asf_abcdefghRAW', created_at: '2026-09-18T00:00:00Z' })
        const created = await apiTokenService.create('HA')
        expect(apiClient.post).toHaveBeenCalledWith('/auth/api-tokens', { name: 'HA' })
        expect(created.token).toBe('asf_abcdefghRAW')
    })

    it('revokes a token by id', async () => {
        vi.mocked(apiClient.delete).mockResolvedValue(undefined)
        await apiTokenService.revoke(7)
        expect(apiClient.delete).toHaveBeenCalledWith('/auth/api-tokens/7')
    })
})
