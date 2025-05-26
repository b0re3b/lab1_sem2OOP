import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/core/api'
import { showToast } from '@/core/utils'

export const useCrewStore = defineStore('crew', () => {
  const crewMembers = ref([])
  const positions = ref([])
  const loading = ref(false)
  const error = ref(null)
  const currentCrewMember = ref(null)
  const workloadStats = ref([])

  // Computed
  const availableCrewMembers = computed(() =>
    crewMembers.value.filter(member => member.is_available)
  )

  const crewByPosition = computed(() => {
    const grouped = {}
    crewMembers.value.forEach(member => {
      const position = member.position?.position_name || 'Unknown'
      if (!grouped[position]) {
        grouped[position] = []
      }
      grouped[position].push(member)
    })
    return grouped
  })

  // Actions
  const fetchCrewMembers = async (filters = {}) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/crew', { params: filters })
      crewMembers.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch crew members'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchCrewMember = async (id) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/crew/${id}`)
      currentCrewMember.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch crew member'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchCrewMemberByEmployeeId = async (employeeId) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/crew/employee/${employeeId}`)
      currentCrewMember.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch crew member'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const createCrewMember = async (crewMemberData) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.post('/crew', crewMemberData)
      crewMembers.value.push(response.data)
      showToast('Crew member created successfully', 'success')
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create crew member'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateCrewMember = async (id, updateData) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.put(`/crew/${id}`, updateData)
      const index = crewMembers.value.findIndex(member => member.id === id)
      if (index !== -1) {
        crewMembers.value[index] = response.data
      }
      currentCrewMember.value = response.data
      showToast('Crew member updated successfully', 'success')
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update crew member'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const setCrewAvailability = async (id, isAvailable) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.put(`/crew/${id}/availability`, {
        is_available: isAvailable
      })
      const index = crewMembers.value.findIndex(member => member.id === id)
      if (index !== -1) {
        crewMembers.value[index].is_available = isAvailable
      }
      showToast(
        `Crew member ${isAvailable ? 'activated' : 'deactivated'} successfully`,
        'success'
      )
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update availability'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchPositions = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/crew/positions')
      positions.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch positions'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchPosition = async (id) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/crew/positions/${id}`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch position'
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
      const response = await api.get(`/crew/available/${flightId}`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch available crew'
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
      const response = await api.get('/crew/workload-statistics', {
        params: { start_date: startDate, end_date: endDate }
      })
      workloadStats.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch workload statistics'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const checkCrewAvailability = async (crewMemberId, flightId) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/crew/${crewMemberId}/availability/${flightId}`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to check availability'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const getCrewRecommendations = async (flightId) => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/crew/recommendations/${flightId}`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to get recommendations'
      showToast(error.value, 'error')
      throw err
    } finally {
      loading.value = false
    }
  }

  const clearCurrentCrewMember = () => {
    currentCrewMember.value = null
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    crewMembers,
    positions,
    loading,
    error,
    currentCrewMember,
    workloadStats,

    // Computed
    availableCrewMembers,
    crewByPosition,

    // Actions
    fetchCrewMembers,
    fetchCrewMember,
    fetchCrewMemberByEmployeeId,
    createCrewMember,
    updateCrewMember,
    setCrewAvailability,
    fetchPositions,
    fetchPosition,
    fetchAvailableCrewForFlight,
    fetchCrewWorkloadStats,
    checkCrewAvailability,
    getCrewRecommendations,
    clearCurrentCrewMember,
    clearError
  }
})
