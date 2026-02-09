import { describe, it, expect, vi, beforeEach, Mock } from 'vitest'
import { apiClient } from './api-client'

describe('API Client Infrastructure', () => {
    beforeEach(() => {
        vi.stubGlobal('fetch', vi.fn())
    })

    it('should make a GET request to the correct URL with credentials', async () => {
        const mockResponse = { data: 'test' }
            ; (fetch as Mock).mockResolvedValue({
                ok: true,
                json: async () => mockResponse,
            })

        const result = await apiClient.get('/test-endpoint')

        expect(fetch).toHaveBeenCalledWith(
            expect.stringContaining('/test-endpoint'),
            expect.objectContaining({
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
        )
        expect(result).toEqual(mockResponse)
    })

    it('should make a POST request with a body and credentials', async () => {
        const mockBody = { name: 'John' }
            ; (fetch as Mock).mockResolvedValue({
                ok: true,
                json: async () => ({ success: true }),
            })

        await apiClient.post('/submit', mockBody)

        expect(fetch).toHaveBeenCalledWith(
            expect.stringContaining('/submit'),
            expect.objectContaining({
                method: 'POST',
                body: JSON.stringify(mockBody),
                credentials: 'include',
            })
        )
    })

    it('should throw an error if the response is not ok', async () => {
        ; (fetch as any).mockResolvedValue({
            ok: false,
            status: 401,
            statusText: 'Unauthorized',
        })

        await expect(apiClient.get('/private')).rejects.toThrow('API Error: 401 Unauthorized')
    })
})
