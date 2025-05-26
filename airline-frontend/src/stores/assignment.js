import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/core/api'
import { showToast } from '@/core/utils'

export const useAssignmentsStore = defineStore('assignments', () => {
  const assignments = ref([])
  const loading = ref(false)
  const error = ref(null)
  const currentAssignment = ref(null)
  const assignmentSummary = ref(null)
  const crewWorkloadStats = ref([])
  const flightCrewStats = ref([])

  // Computed
  const activeAssignments = computed(() =>
    assignments.value.filter(assignment => assignment.status === 'ASSIGNED')
  )

  const confirmedAssignments = computed(() =>
    assignments.value.filter(assignment => assignment.status === 'CONFIRMED')
  )

  const assignmentsByStatus = computed(() => {
    const grouped = {}
    assignments.value.forEach(assignment => {
      const status = assignment.status
      if (!grouped[status]) {
        grouped[status] = []
      }
      grouped[status].push(assignment)
    })
    return grouped
  })

  const assignmentsByFlight = computed(() => {
    const grouped = {}
    assignments.value.forEach(assignment => {
      const flightNumber = assignment.flight?.flight_number || 'Unknown'
      if (!grouped[flightNumber]) {
        grouped[flightNumber] = []
      }
      grouped[flightNumber].push(assignment)
    })
    return grouped
  })

  // Actions
  const fetchAssignments = async (filters = {}) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/assignments', { params: filters })
      assignments.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch assignments'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchAssignment = async (id) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/assignments/${id}`)
      currentAssignment.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch assignment'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchAssignmentsByFlight = async (flightId) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/assignments/flight/${flightId}`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch flight assignments'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchAssignmentsByCrewMember = async (crewMemberId) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/assignments/crew/${crewMemberId}`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch crew assignments'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchAssignmentsByDateRange = async (startDate, endDate) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/assignments/date-range', {
        params: { start_date: startDate, end_date: endDate }
      })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch assignments by date range'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const createAssignment = async (assignmentData) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.post('/assignments', assignmentData)
      assignments.value.push(response.data)
      showToast('Assignment created successfully', 'success')
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create assignment'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateAssignment = async (id, updateData) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.put(`/assignments/${id}`, updateData)
      const index = assignments.value.findIndex(assignment => assignment.id === id)
      if (index !== -1) {
        assignments.value[index] = response.data
      }
      currentAssignment.value = response.data
      showToast('Assignment updated successfully', 'success')
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update assignment'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const cancelAssignment = async (id, reason = '') => {
    loading.value = true
    error.value = null
    try {
      const response = await api.put(`/assignments/${id}/cancel`, { reason })
      const index = assignments.value.findIndex(assignment => assignment.id === id)
      if (index !== -1) {
        assignments.value[index].status = 'CANCELLED'
      }
      showToast('Assignment cancelled successfully', 'success')
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to cancel assignment'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const confirmAssignment = async (id) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.put(`/assignments/${id}/confirm`)
      const index = assignments.value.findIndex(assignment => assignment.id === id)
      if (index !== -1) {
        assignments.value[index].status = 'CONFIRMED'
      }
      showToast('Assignment confirmed successfully', 'success')
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to confirm assignment'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const autoAssignCrew = async (flightId) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.post(`/assignments/auto-assign/${flightId}`)
      // Refresh assignments after auto-assignment
      await fetchAssignments()
      showToast('Crew auto-assigned successfully', 'success')
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to auto-assign crew'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchAssignmentSummary = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/assignments/summary')
      assignmentSummary.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch assignment summary'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchCrewWorkloadStats = async (startDate, endDate) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/assignments/crew-workload-statistics', {
        params: { start_date: startDate, end_date: endDate }
      })
      crewWorkloadStats.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch crew workload statistics'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchFlightCrewStats = async (startDate, endDate) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/assignments/flight-crew-statistics', {
        params: { start_date: startDate, end_date: endDate }
      })
      flightCrewStats.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch flight crew statistics'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchAvailableCrewForFlight = async (flightId) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/assignments/available-crew/${flightId}`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch available crew for flight'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const clearCurrentAssignment = () => {
    currentAssignment.value = null
  }

  const clearError = () => {
    error.value = null
  }

  const removeAssignmentFromList = (assignmentId) => {
    const index = assignments.value.findIndex(assignment => assignment.id === assignmentId)
    if (index !== -1) {
      assignments.value.splice(index, 1)
    }
  }

  return {
    // State
    assignments,
    loading,
    error,
    currentAssignment,
    assignmentSummary,
    crewWorkloadStats,
    flightCrewStats,

    // Computed
    activeAssignments,
    confirmedAssignments,
    assignmentsByStatus,
    assignmentsByFlight,

    // Actions
    fetchAssignments,
    fetchAssignment,
    fetchAssignmentsByFlight,
    fetchAssignmentsByCrewMember,
    fetchAssignmentsByDateRange,
    createAssignment,
    updateAssignment,
    cancelAssignment,
    confirmAssignment,
    autoAssignCrew,
    fetchAssignmentSummary,
    fetchCrewWorkloadStats,
    fetchFlightCrewStats,
    fetchAvailableCrewForFlight,
    clearCurrentAssignment,
    clearError,
    removeAssignmentFromList
  }
})
