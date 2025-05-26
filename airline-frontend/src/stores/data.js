import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/core/api'
import { useAppStore } from './app'

export const useDataStore = defineStore('data', () => {
  const appStore = useAppStore()

  // Flights State
  const flights = ref([])
  const currentFlight = ref(null)
  const flightStatistics = ref({})

  // Crew State
  const crewMembers = ref([])
  const crewPositions = ref([])
  const currentCrewMember = ref(null)
  const availableCrew = ref([])

  // Assignments State
  const assignments = ref([])
  const currentAssignment = ref(null)
  const assignmentSummary = ref({})

  // Cache timestamps for data freshness
  const lastUpdated = ref({
    flights: null,
    crew: null,
    assignments: null,
    positions: null
  })

  // Getters
  const getFlights = computed(() => flights.value)
  const getFlightById = computed(() => (id) =>
    flights.value.find(f => f.id === id)
  )
  const getFlightByNumber = computed(() => (number) =>
    flights.value.find(f => f.flight_number === number)
  )

  const getCrewMembers = computed(() => crewMembers.value)
  const getCrewMemberById = computed(() => (id) =>
    crewMembers.value.find(cm => cm.id === id)
  )
  const getCrewMembersByPosition = computed(() => (positionId) =>
    crewMembers.value.filter(cm => cm.position_id === positionId)
  )

  const getAssignments = computed(() => assignments.value)
  const getAssignmentsByFlight = computed(() => (flightId) =>
    assignments.value.filter(a => a.flight_id === flightId)
  )
  const getAssignmentsByCrewMember = computed(() => (crewMemberId) =>
    assignments.value.filter(a => a.crew_member_id === crewMemberId)
  )

  // Utility getters
  const getFlightsNeedingCrew = computed(() =>
    flights.value.filter(f => {
      const assignedCount = assignments.value.filter(a =>
        a.flight_id === f.id && a.status === 'ASSIGNED'
      ).length
      return assignedCount < f.crew_required
    })
  )

  const getAvailableCrewForFlight = computed(() => (flightId) => {
    const flight = getFlightById.value(flightId)
    if (!flight) return []

    return crewMembers.value.filter(cm => {
      if (!cm.is_available) return false

      // Перевіряємо конфлікти розкладу
      const hasConflict = assignments.value.some(a => {
        if (a.crew_member_id !== cm.id || a.status !== 'ASSIGNED') return false

        const assignmentFlight = getFlightById.value(a.flight_id)
        if (!assignmentFlight) return false

        const flightStart = new Date(flight.departure_time)
        const flightEnd = new Date(flight.arrival_time)
        const assignmentStart = new Date(assignmentFlight.departure_time)
        const assignmentEnd = new Date(assignmentFlight.arrival_time)

        return (flightStart < assignmentEnd && flightEnd > assignmentStart)
      })

      return !hasConflict
    })
  })

  // Flight Actions
  const fetchFlights = async (params = {}) => {
    try {
      appStore.startLoading()
      const response = await api.get('/api/flights', { params })
      flights.value = response.data.data || response.data
      lastUpdated.value.flights = new Date()
      return response.data
    } catch (error) {
      appStore.showError('Помилка завантаження рейсів: ' + error.message)
      throw error
    } finally {
      appStore.stopLoading()
    }
  }

  const fetchFlightById = async (id) => {
    try {
      const response = await api.get(`/api/flights/${id}`)
      currentFlight.value = response.data
      return response.data
    } catch (error) {
      appStore.showError('Помилка завантаження рейсу: ' + error.message)
      throw error
    }
  }

  const createFlight = async (flightData) => {
    try {
      appStore.startLoading()
      const response = await api.post('/api/flights', flightData)
      flights.value.push(response.data)
      appStore.showSuccess('Рейс успішно створено')
      return response.data
    } catch (error) {
      appStore.showError('Помилка створення рейсу: ' + error.message)
      throw error
    } finally {
      appStore.stopLoading()
    }
  }

  const updateFlight = async (id, flightData) => {
    try {
      appStore.startLoading()
      const response = await api.put(`/api/flights/${id}`, flightData)
      const index = flights.value.findIndex(f => f.id === id)
      if (index !== -1) {
        flights.value[index] = response.data
      }
      appStore.showSuccess('Рейс успішно оновлено')
      return response.data
    } catch (error) {
      appStore.showError('Помилка оновлення рейсу: ' + error.message)
      throw error
    } finally {
      appStore.stopLoading()
    }
  }

  const deleteFlight = async (id) => {
    try {
      appStore.startLoading()
      await api.delete(`/api/flights/${id}`)
      const index = flights.value.findIndex(f => f.id === id)
      if (index !== -1) {
        flights.value.splice(index, 1)
      }
      appStore.showSuccess('Рейс успішно видалено')
    } catch (error) {
      appStore.showError('Помилка видалення рейсу: ' + error.message)
      throw error
    } finally {
      appStore.stopLoading()
    }
  }

  // Crew Actions
  const fetchCrewMembers = async (params = {}) => {
    try {
      appStore.startLoading()
      const response = await api.get('/api/crew', { params })
      crewMembers.value = response.data.data || response.data
      lastUpdated.value.crew = new Date()
      return response.data
    } catch (error) {
      appStore.showError('Помилка завантаження екіпажу: ' + error.message)
      throw error
    } finally {
      appStore.stopLoading()
    }
  }

  const fetchCrewPositions = async () => {
    try {
      const response = await api.get('/api/crew/positions')
      crewPositions.value = response.data.data || response.data
      lastUpdated.value.positions = new Date()
      return response.data
    } catch (error) {
      appStore.showError('Помилка завантаження посад: ' + error.message)
      throw error
    }
  }

  const createCrewMember = async (crewData) => {
    try {
      appStore.startLoading()
      const response = await api.post('/api/crew', crewData)
      crewMembers.value.push(response.data)
      appStore.showSuccess('Член екіпажу успішно створений')
      return response.data
    } catch (error) {
      appStore.showError('Помилка створення члена екіпажу: ' + error.message)
      throw error
    } finally {
      appStore.stopLoading()
    }
  }

  const updateCrewMember = async (id, crewData) => {
    try {
      appStore.startLoading()
      const response = await api.put(`/api/crew/${id}`, crewData)
      const index = crewMembers.value.findIndex(cm => cm.id === id)
      if (index !== -1) {
        crewMembers.value[index] = response.data
      }
      appStore.showSuccess('Дані члена екіпажу успішно оновлено')
      return response.data
    } catch (error) {
      appStore.showError('Помилка оновлення члена екіпажу: ' + error.message)
      throw error
    } finally {
      appStore.stopLoading()
    }
  }

  const setCrewAvailability = async (id, isAvailable) => {
    try {
      const response = await api.patch(`/api/crew/${id}/availability`, {
        is_available: isAvailable
      })
      const index = crewMembers.value.findIndex(cm => cm.id === id)
      if (index !== -1) {
        crewMembers.value[index].is_available = isAvailable
      }
      appStore.showSuccess(`Доступність ${isAvailable ? 'увімкнено' : 'вимкнено'}`)
      return response.data
    } catch (error) {
      appStore.showError('Помилка зміни доступності: ' + error.message)
      throw error
    }
  }

  const fetchAvailableCrew = async (flightId) => {
    try {
      const response = await api.get(`/api/assignments/available-crew/${flightId}`)
      availableCrew.value = response.data.data || response.data
      return response.data
    } catch (error) {
      appStore.showError('Помилка завантаження доступного екіпажу: ' + error.message)
      throw error
    }
  }

  // Assignment Actions
  const fetchAssignments = async (params = {}) => {
    try {
      appStore.startLoading()
      const response = await api.get('/api/assignments', { params })
      assignments.value = response.data.data || response.data
      lastUpdated.value.assignments = new Date()
      return response.data
    } catch (error) {
      appStore.showError('Помилка завантаження призначень: ' + error.message)
      throw error
    } finally {
      appStore.stopLoading()
    }
  }

  const createAssignment = async (assignmentData) => {
    try {
      appStore.startLoading()
      const response = await api.post('/api/assignments', assignmentData)
      assignments.value.push(response.data)
      appStore.showSuccess('Призначення успішно створено')
      return response.data
    } catch (error) {
      appStore.showError('Помилка створення призначення: ' + error.message)
      throw error
    } finally {
      appStore.stopLoading()
    }
  }

  const updateAssignment = async (id, assignmentData) => {
    try {
      appStore.startLoading()
      const response = await api.put(`/api/assignments/${id}`, assignmentData)
      const index = assignments.value.findIndex(a => a.id === id)
      if (index !== -1) {
        assignments.value[index] = response.data
      }
      appStore.showSuccess('Призначення успішно оновлено')
      return response.data
    } catch (error) {
      appStore.showError('Помилка оновлення призначення: ' + error.message)
      throw error
    } finally {
      appStore.stopLoading()
    }
  }

  const cancelAssignment = async (id) => {
    try {
      appStore.startLoading()
      const response = await api.patch(`/api/assignments/${id}/cancel`)
      const index = assignments.value.findIndex(a => a.id === id)
      if (index !== -1) {
        assignments.value[index].status = 'CANCELLED'
      }
      appStore.showSuccess('Призначення скасовано')
      return response.data
    } catch (error) {
      appStore.showError('Помилка скасування призначення: ' + error.message)
      throw error
    } finally {
      appStore.stopLoading()
    }
  }

  const autoAssignCrew = async (flightId) => {
    try {
      appStore.startLoading()
      const response = await api.post(`/api/assignments/auto-assign/${flightId}`)
      await fetchAssignments() // Оновлюємо список призначень
      appStore.showSuccess('Екіпаж автоматично призначено')
      return response.data
    } catch (error) {
      appStore.showError('Помилка автопризначення: ' + error.message)
      throw error
    } finally {
      appStore.stopLoading()
    }
  }

  // Statistics Actions
  const fetchFlightStatistics = async () => {
    try {
      const response = await api.get('/api/assignments/flight-statistics')
      flightStatistics.value = response.data
      return response.data
    } catch (error) {
      appStore.showError('Помилка завантаження статистики: ' + error.message)
      throw error
    }
  }

  const fetchAssignmentSummary = async (params = {}) => {
    try {
      const response = await api.get('/api/assignments/summary', { params })
      assignmentSummary.value = response.data
      return response.data
    } catch (error) {
      appStore.showError('Помилка завантаження сумарної інформації: ' + error.message)
      throw error
    }
  }

  // Utility Actions
  const refreshAllData = async () => {
    try {
      appStore.startLoading()
      await Promise.all([
        fetchFlights(),
        fetchCrewMembers(),
        fetchAssignments(),
        fetchCrewPositions()
      ])
      appStore.showSuccess('Дані оновлено')
    } catch (error) {
      appStore.showError('Помилка оновлення даних: ' + error.message)
    } finally {
      appStore.stopLoading()
    }
  }

  const isDataFresh = (dataType, maxAgeMinutes = 5) => {
    const lastUpdate = lastUpdated.value[dataType]
    if (!lastUpdate) return false

    const now = new Date()
    const diffMinutes = (now - lastUpdate) / (1000 * 60)
    return diffMinutes < maxAgeMinutes
  }

  const clearCache = () => {
    flights.value = []
    crewMembers.value = []
    assignments.value = []
    crewPositions.value = []
    availableCrew.value = []
    currentFlight.value = null
    currentCrewMember.value = null
    currentAssignment.value = null
    flightStatistics.value = {}
    assignmentSummary.value = {}
    lastUpdated.value = {
      flights: null,
      crew: null,
      assignments: null,
      positions: null
    }
  }

  return {
    // State
    flights,
    crewMembers,
    crewPositions,
    assignments,
    availableCrew,
    currentFlight,
    currentCrewMember,
    currentAssignment,
    flightStatistics,
    assignmentSummary,
    lastUpdated,

    // Getters
    getFlights,
    getFlightById,
    getFlightByNumber,
    getCrewMembers,
    getCrewMemberById,
    getCrewMembersByPosition,
    getAssignments,
    getAssignmentsByFlight,
    getAssignmentsByCrewMember,
    getFlightsNeedingCrew,
    getAvailableCrewForFlight,

    // Actions
    fetchFlights,
    fetchFlightById,
    createFlight,
    updateFlight,
    deleteFlight,
    fetchCrewMembers,
    fetchCrewPositions,
    createCrewMember,
    updateCrewMember,
    setCrewAvailability,
    fetchAvailableCrew,
    fetchAssignments,
    createAssignment,
    updateAssignment,
    cancelAssignment,
    autoAssignCrew,
    fetchFlightStatistics,
    fetchAssignmentSummary,
    refreshAllData,
    isDataFresh,
    clearCache
  }
})
