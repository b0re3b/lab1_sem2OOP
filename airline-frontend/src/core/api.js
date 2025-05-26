import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import router from '../router'
import { useToast } from 'vue-toastification'

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    const token = authStore.accessToken

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add request timestamp for logging
    config.metadata = { startTime: new Date() }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response) => {
    // Log successful requests in development
    if (import.meta.env.DEV) {
      const duration = new Date() - response.config.metadata.startTime
      console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status} (${duration}ms)`)
    }

    return response
  },
  async (error) => {
    const originalRequest = error.config
    const authStore = useAuthStore()
    const toast = useToast()

    // Log errors in development
    if (import.meta.env.DEV) {
      const duration = new Date() - originalRequest.metadata?.startTime
      console.error(`❌ ${originalRequest.method?.toUpperCase()} ${originalRequest.url} - ${error.response?.status} (${duration}ms)`)
    }

    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Try to refresh token
        await authStore.refreshToken()

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${authStore.accessToken}`
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, redirect to login
        authStore.logout()
        router.push('/login')
        toast.error('Сесія закінчилася. Будь ласка, увійдіть знову.')
        return Promise.reject(refreshError)
      }
    }

    // Handle other HTTP errors
    const errorMessage = getErrorMessage(error)

    if (error.response?.status >= 500) {
      toast.error('Помилка сервера. Спробуйте пізніше.')
    } else if (error.response?.status === 403) {
      toast.error('У вас немає прав для виконання цієї дії')
    } else if (error.response?.status === 404) {
      toast.error('Ресурс не знайдено')
    } else if (error.response?.status >= 400) {
      toast.error(errorMessage || 'Помилка запиту')
    }

    return Promise.reject(error)
  }
)

// Helper function to extract error message
function getErrorMessage(error) {
  if (error.response?.data?.detail) {
    return error.response.data.detail
  }

  if (error.response?.data?.message) {
    return error.response.data.message
  }

  if (error.response?.data?.error) {
    return error.response.data.error
  }

  if (error.message) {
    return error.message
  }

  return 'Невідома помилка'
}

// API endpoints
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  refreshToken: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  getCurrentUser: () => api.get('/auth/me'),
  keycloakLogin: () => api.get('/auth/keycloak/login'),
  keycloakCallback: (code, state) => api.post('/auth/keycloak/callback', { code, state }),
  keycloakLogout: () => api.post('/auth/keycloak/logout'),
}

export const flightAPI = {
  create: (data) => api.post('/flights', data),
  getById: (id) => api.get(`/flights/${id}`),
  getByNumber: (number) => api.get(`/flights/number/${number}`),
  getAll: (params) => api.get('/flights', { params }),
  getNeedingCrew: () => api.get('/flights/needing-crew'),
  getDailySchedule: (date) => api.get(`/flights/schedule/${date}`),
  update: (id, data) => api.put(`/flights/${id}`, data),
  updateStatus: (id, status) => api.patch(`/flights/${id}/status`, { status }),
  delete: (id) => api.delete(`/flights/${id}`),
  getCrewSummary: (id) => api.get(`/flights/${id}/crew-summary`),
}

export const crewAPI = {
  create: (data) => api.post('/crew', data),
  getById: (id) => api.get(`/crew/${id}`),
  getByEmployeeId: (employeeId) => api.get(`/crew/employee/${employeeId}`),
  getAvailable: (params) => api.get('/crew/available', { params }),
  update: (id, data) => api.put(`/crew/${id}`, data),
  setAvailability: (id, available) => api.patch(`/crew/${id}/availability`, { is_available: available }),
  getPositions: () => api.get('/crew/positions'),
  getPosition: (id) => api.get(`/crew/positions/${id}`),
  getWorkloadStats: () => api.get('/crew/workload-statistics'),
  checkAvailability: (id, flightId) => api.get(`/crew/${id}/check-availability/${flightId}`),
  getRecommendations: (flightId) => api.get(`/crew/recommendations/${flightId}`),
}

export const assignmentAPI = {
  create: (data) => api.post('/assignments', data),
  getById: (id) => api.get(`/assignments/${id}`),
  getAll: (params) => api.get('/assignments', { params }),
  getByFlight: (flightId) => api.get(`/assignments/flight/${flightId}`),
  getByCrew: (crewId) => api.get(`/assignments/crew/${crewId}`),
  getByDateRange: (startDate, endDate) => api.get(`/assignments/date-range/${startDate}/${endDate}`),
  update: (id, data) => api.put(`/assignments/${id}`, data),
  cancel: (id) => api.patch(`/assignments/${id}/cancel`),
  autoAssign: (flightId) => api.post(`/assignments/auto-assign/${flightId}`),
  getSummary: () => api.get('/assignments/summary'),
  getCrewWorkload: () => api.get('/assignments/crew-workload'),
  getFlightStats: () => api.get('/assignments/flight-statistics'),
  getAvailableForFlight: (flightId) => api.get(`/assignments/available-crew/${flightId}`),
  confirm: (id) => api.patch(`/assignments/${id}/confirm`),
}

export default api
