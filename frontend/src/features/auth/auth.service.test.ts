import { describe, it, expect, vi, beforeEach } from 'vitest'
import { authService } from './auth.service'
import { apiClient } from '@/infrastructure/api-client'

// Mock the global infrastructure API client
vi.mock('@/infrastructure/api-client', () => ({
    apiClient: {
        post: vi.fn()
    }
}))

describe('Auth Service (Local Scope)', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('should call the correct login endpoint and return success', async () => {
        const mockResponse = { access_token: 'fake-token', user: { email: 'test@example.com' } }
        vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

        const result = await authService.login('test@example.com', 'password123')

        expect(apiClient.post).toHaveBeenCalledWith('/auth/token', {
            username: 'test@example.com',
            password: 'password123'
        })
        expect(result).toEqual(mockResponse)
    })

    it('should throw an error if login fails', async () => {
        vi.mocked(apiClient.post).mockRejectedValue(new Error('Invalid credentials'))

        await expect(authService.login('wrong@example.com', 'wrong'))
            .rejects.toThrow('Invalid credentials')
    })
})
