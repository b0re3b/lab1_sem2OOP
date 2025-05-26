import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/core/api'
import { errorUtils, dateUtils } from '@/core/utils'

export const useFlightsStore = defineStore('flights', () => {
  // State
  const flights = ref([])
  const currentFlight = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 0
  })
  const filters = ref({
    status: '',
    dateFrom: '',
    dateTo: '',
    departureCity: '',
    arrivalCity: '',
    flightNumber: ''
  })

  // Getters
  const flightsList = computed(() => flights.value)
  const isLoading = computed(() => loading.value)
  const hasError = computed(() => !!error.value)
  const totalFlights = computed(() => pagination.value.total)

  const flightsByStatus = computed(() => {
    return flights.value.reduce((acc, flight) => {
      const status = flight.status
      if (!acc[status]) acc[status] = []
      acc[status].push(flight)
      return acc
    }, {})
  })

  const todayFlights = computed(() => {
    return flights.value.filter(flight =>
      dateUtils.isToday(flight.departure_time)
    )
  })

  const upcomingFlights = computed(() => {
    const now = new Date()
    return flights.value.filter(flight =>
      new Date(flight.departure_time) > now
    ).sort((a, b) => new Date(a.departure_time) - new Date(b.departure_time))
  })

  // Actions
  async function fetchFlights(params = {}) {
    loading.value = true
    error.value = null

    try {
      const queryParams = {
        page: pagination.value.page,
        limit: pagination.value.limit,
        ...filters.value,
        ...params
      }

      // Remove empty filters
      Object.keys(queryParams).forEach(key => {
        if (queryParams[key] === '' || queryParams[key] === null) {
          delete queryParams[key]
        }
      })

      const response = await api.get('/flights', { params: queryParams })

      flights.value = response.data.flights || response.data

      if (response.data.pagination) {
        pagination.value = { ...pagination.value, ...response.data.pagination }
      }

      return response.data
    } catch (err) {
      error.value = errorUtils.getErrorMessage(err)
      console.error('Error fetching flights:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchFlightById(id) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/flights/${id}`)
      currentFlight.value = response.data
      return response.data
    } catch (err) {
      error.value = errorUtils.getErrorMessage(err)
      console.error('Error fetching flight:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchFlightByNumber(flightNumber) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/flights/number/${flightNumber}`)
      currentFlight.value = response.data
      return response.data
    } catch (err) {
      error.value = errorUtils.getErrorMessage(err)
      console.error('Error fetching flight by number:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createFlight(flightData) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/flights', flightData)
      const newFlight = response.data

      flights.value.unshift(newFlight)
      currentFlight.value = newFlight

      return newFlight
    } catch (err) {
      error.value = errorUtils.getErrorMessage(err)
      console.error('Error creating flight:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateFlight(id, flightData) {
    loading.value = true
    error.value = null

    try {
      const response = await api.put(`/flights/${id}`, flightData)
      const updatedFlight = response.data

      const index = flights.value.findIndex(f => f.id === id)
      if (index !== -1) {
        flights.value[index] = updatedFlight
      }

      if (currentFlight.value?.id === id) {
        currentFlight.value = updatedFlight
      }

      return updatedFlight
    } catch (err) {
      error.value = errorUtils.getErrorMessage(err)
      console.error('Error updating flight:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateFlightStatus(id, status) {
    loading.value = true
    error.value = null

    try {
      const response = await api.patch(`/flights/${id}/status`, { status })
      const updatedFlight = response.data

      const index = flights.value.findIndex(f => f.id === id)
      if (index !== -1) {
        flights.value[index] = { ...flights.value[index], status }
      }

      if (currentFlight.value?.id === id) {
        currentFlight.value = { ...currentFlight.value, status }
      }

      return updatedFlight
    } catch (err) {
      error.value = errorUtils.getErrorMessage(err)
      console.error('Error updating flight status:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteFlight(id) {
    loading.value = true
    error.value = null

    try {
      await api.delete(`/flights/${id}`)

      flights.value = flights.value.filter(f => f.id !== id)

      if (currentFlight.value?.id === id) {
        currentFlight.value = null
      }

      return true
    } catch (err) {
      error.value = errorUtils.getErrorMessage(err)
      console.error('Error deleting flight:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchFlightsNeedingCrew() {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/flights/needing-crew')
      return response.data
    } catch (err) {
      error.value = errorUtils.getErrorMessage(err)
      console.error('Error fetching flights needing crew:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchDailySchedule(date) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/flights/daily-schedule`, {
        params: { date }
      })
      return response.data
    } catch (err) {
      error.value = errorUtils.getErrorMessage(err)
      console.error('Error fetching daily schedule:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchFlightCrewSummary(id) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/flights/${id}/crew-summary`)
      return response.data
    } catch (err) {
      error.value = errorUtils.getErrorMessage(err)
      console.error('Error fetching flight crew summary:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  // Utility functions
  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
  }

  function clearFilters() {
    filters.value = {
      status: '',
      dateFrom: '',
      dateTo: '',
      departureCity: '',
      arrivalCity: '',
      flightNumber: ''
    }
  }

  function setPage(page) {
    pagination.value.page = page
  }

  function setLimit(limit) {
    pagination.value.limit = limit
    pagination.value.page = 1 // Reset to first page
  }

  function clearError() {
    error.value = null
  }

  function setCurrentFlight(flight) {
    currentFlight.value = flight
  }

  function clearCurrentFlight() {
    currentFlight.value = null
  }

  // Reset store
  function $reset() {
    flights.value = []
    currentFlight.value = null
    loading.value = false
    error.value = null
    pagination.value = {
      page: 1,
      limit: 20,
      total: 0,
      totalPages: 0
    }
    clearFilters()
  }

  return {
    // State
    flights: flightsList,
    currentFlight,
    loading,
    error,
    pagination,
    filters,

    // Getters
    isLoading,
    hasError,
    totalFlights,
    flightsByStatus,
    todayFlights,
    upcomingFlights,

    // Actions
    fetchFlights,
    fetchFlightById,
    fetchFlightByNumber,
    createFlight,
    updateFlight,
    updateFlightStatus,
    deleteFlight,
    fetchFlightsNeedingCrew,
    fetchDailySchedule,
    fetchFlightCrewSummary,

    // Utilities
    setFilters,
    clearFilters,
    setPage,
    setLimit,
    clearError,
    setCurrentFlight,
    clearCurrentFlight,
    $reset
  }
})
