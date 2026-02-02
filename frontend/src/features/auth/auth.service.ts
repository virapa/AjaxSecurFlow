import { apiClient } from '@/infrastructure/api-client'

/**
 * Auth Service (Local Scope: features/auth)
 * Handles authentication business logic.
 */
export const authService = {
    /**
     * authenticates a user with Ajax email and password.
     * The backend is expected to set HTTPOnly cookies for security.
     */
    login: async (email: string, password: string) => {
        return apiClient.post('/auth/token', {
            username: email,
            password: password
        })
    },

    /**
     * Clears the session.
     */
    logout: async () => {
        return apiClient.post('/auth/logout', {})
    }
}
