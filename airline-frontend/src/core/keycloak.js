import Keycloak from 'keycloak-js'
import { useAuthStore } from '@/stores/auth'

// Keycloak configuration
const keycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'airline',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'airline-frontend'
}

// Initialize Keycloak instance
const keycloak = new Keycloak(keycloakConfig)

class KeycloakService {
  constructor() {
    this.keycloak = keycloak
    this.isInitialized = false
  }

  /**
   * Initialize Keycloak
   */
  async init() {
    try {
      const authenticated = await this.keycloak.init({
        onLoad: 'check-sso',
        silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
        pkceMethod: 'S256',
        checkLoginIframe: false
      })

      this.isInitialized = true

      // Setup token refresh
      this.setupTokenRefresh()

      // Setup auth store
      const authStore = useAuthStore()
      if (authenticated) {
        await authStore.setKeycloakAuth(this.keycloak)
      }

      return authenticated
    } catch (error) {
      console.error('Failed to initialize Keycloak:', error)
      throw error
    }
  }

  /**
   * Login via Keycloak
   */
  async login() {
    try {
      await this.keycloak.login({
        redirectUri: window.location.origin
      })
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  /**
   * Logout from Keycloak
   */
  async logout() {
    try {
      const authStore = useAuthStore()
      await authStore.logout()

      await this.keycloak.logout({
        redirectUri: window.location.origin
      })
    } catch (error) {
      console.error('Logout failed:', error)
      throw error
    }
  }

  /**
   * Get current user info
   */
  async getUserInfo() {
    if (!this.isAuthenticated()) {
      return null
    }

    try {
      return await this.keycloak.loadUserInfo()
    } catch (error) {
      console.error('Failed to load user info:', error)
      return null
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return this.keycloak.authenticated || false
  }

  /**
   * Get access token
   */
  getToken() {
    return this.keycloak.token
  }

  /**
   * Get refresh token
   */
  getRefreshToken() {
    return this.keycloak.refreshToken
  }

  /**
   * Check if user has role
   */
  hasRole(role) {
    if (!this.isAuthenticated()) {
      return false
    }

    const realmRoles = this.keycloak.realmAccess?.roles || []
    const clientRoles = this.keycloak.resourceAccess?.[keycloakConfig.clientId]?.roles || []

    return realmRoles.includes(role) || clientRoles.includes(role)
  }

  /**
   * Check if user is admin
   */
  isAdmin() {
    return this.hasRole('ADMIN')
  }

  /**
   * Check if user is dispatcher
   */
  isDispatcher() {
    return this.hasRole('DISPATCHER')
  }

  /**
   * Get user roles
   */
  getUserRoles() {
    if (!this.isAuthenticated()) {
      return []
    }

    const realmRoles = this.keycloak.realmAccess?.roles || []
    const clientRoles = this.keycloak.resourceAccess?.[keycloakConfig.clientId]?.roles || []

    return [...realmRoles, ...clientRoles]
  }

  /**
   * Update token if needed
   */
  async updateToken(minValidity = 30) {
    try {
      const refreshed = await this.keycloak.updateToken(minValidity)
      if (refreshed) {
        console.log('Token refreshed')
        // Update auth store with new token
        const authStore = useAuthStore()
        authStore.updateToken(this.keycloak.token)
      }
      return refreshed
    } catch (error) {
      console.error('Failed to refresh token:', error)
      // Token refresh failed, redirect to login
      await this.login()
      throw error
    }
  }

  /**
   * Setup automatic token refresh
   */
  setupTokenRefresh() {
    // Refresh token every 5 minutes
    setInterval(async () => {
      if (this.isAuthenticated()) {
        try {
          await this.updateToken(60) // Refresh if expires in 1 minute
        } catch (error) {
          console.error('Token refresh failed:', error)
        }
      }
    }, 5 * 60 * 1000) // 5 minutes

    // Setup Keycloak events
    this.keycloak.onTokenExpired = () => {
      console.log('Token expired')
      this.updateToken()
    }

    this.keycloak.onAuthRefreshSuccess = () => {
      console.log('Auth refresh success')
    }

    this.keycloak.onAuthRefreshError = () => {
      console.log('Auth refresh error')
      this.login()
    }

    this.keycloak.onAuthError = (error) => {
      console.error('Auth error:', error)
    }
  }

  /**
   * Get account management URL
   */
  getAccountUrl() {
    return this.keycloak.createAccountUrl()
  }

  /**
   * Get user profile
   */
  getUserProfile() {
    if (!this.isAuthenticated()) {
      return null
    }

    return {
      id: this.keycloak.subject,
      username: this.keycloak.tokenParsed?.preferred_username,
      email: this.keycloak.tokenParsed?.email,
      firstName: this.keycloak.tokenParsed?.given_name,
      lastName: this.keycloak.tokenParsed?.family_name,
      fullName: this.keycloak.tokenParsed?.name,
      roles: this.getUserRoles()
    }
  }
}

// Export singleton instance
export const keycloakService = new KeycloakService()
export default keycloakService
