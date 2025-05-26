import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  // Стан UI
  const loading = ref(false)
  const sidebarCollapsed = ref(false)
  const darkMode = ref(false)
  const notifications = ref([])
  const currentPage = ref('')
  const breadcrumbs = ref([])

  // Модальні вікна
  const modals = ref({
    createFlight: false,
    editFlight: false,
    createCrewMember: false,
    editCrewMember: false,
    assignCrew: false,
    confirmAction: false
  })

  // Дані для модальних вікон
  const modalData = ref({
    selectedFlight: null,
    selectedCrewMember: null,
    selectedAssignment: null,
    confirmCallback: null,
    confirmMessage: ''
  })

  // Фільтри та пошук
  const filters = ref({
    flights: {
      status: '',
      date: '',
      search: ''
    },
    crew: {
      position: '',
      availability: '',
      search: ''
    },
    assignments: {
      status: '',
      date: '',
      search: ''
    }
  })

  // Пагінація
  const pagination = ref({
    flights: { page: 1, limit: 10, total: 0 },
    crew: { page: 1, limit: 10, total: 0 },
    assignments: { page: 1, limit: 10, total: 0 }
  })

  // Getters
  const isLoading = computed(() => loading.value)
  const isSidebarCollapsed = computed(() => sidebarCollapsed.value)
  const isDarkMode = computed(() => darkMode.value)
  const hasNotifications = computed(() => notifications.value.length > 0)
  const unreadNotifications = computed(() =>
    notifications.value.filter(n => !n.read).length
  )

  // Actions - Loading
  const setLoading = (state) => {
    loading.value = state
  }

  const startLoading = () => setLoading(true)
  const stopLoading = () => setLoading(false)

  // Actions - Sidebar
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const setSidebarCollapsed = (state) => {
    sidebarCollapsed.value = state
  }

  // Actions - Theme
  const toggleDarkMode = () => {
    darkMode.value = !darkMode.value
    localStorage.setItem('darkMode', JSON.stringify(darkMode.value))
  }

  const initTheme = () => {
    const saved = localStorage.getItem('darkMode')
    if (saved) {
      darkMode.value = JSON.parse(saved)
    }
  }

  // Actions - Notifications
  const addNotification = (notification) => {
    const id = Date.now()
    notifications.value.push({
      id,
      read: false,
      timestamp: new Date(),
      ...notification
    })

    // Автоматично видаляємо через 5 секунд якщо не критична
    if (notification.type !== 'error') {
      setTimeout(() => {
        removeNotification(id)
      }, 5000)
    }
  }

  const removeNotification = (id) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  const markNotificationRead = (id) => {
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      notification.read = true
    }
  }

  const clearAllNotifications = () => {
    notifications.value = []
  }

  // Actions - Navigation
  const setCurrentPage = (page) => {
    currentPage.value = page
  }

  const setBreadcrumbs = (crumbs) => {
    breadcrumbs.value = crumbs
  }

  // Actions - Modals
  const openModal = (modalName, data = null) => {
    if (modals.value.hasOwnProperty(modalName)) {
      modals.value[modalName] = true
      if (data) {
        modalData.value = { ...modalData.value, ...data }
      }
    }
  }

  const closeModal = (modalName) => {
    if (modals.value.hasOwnProperty(modalName)) {
      modals.value[modalName] = false
      // Очищуємо дані модального вікна
      if (modalName !== 'confirmAction') {
        modalData.value = {
          selectedFlight: null,
          selectedCrewMember: null,
          selectedAssignment: null,
          confirmCallback: null,
          confirmMessage: ''
        }
      }
    }
  }

  const closeAllModals = () => {
    Object.keys(modals.value).forEach(key => {
      modals.value[key] = false
    })
    modalData.value = {
      selectedFlight: null,
      selectedCrewMember: null,
      selectedAssignment: null,
      confirmCallback: null,
      confirmMessage: ''
    }
  }

  // Actions - Filters
  const setFilter = (section, key, value) => {
    if (filters.value[section]) {
      filters.value[section][key] = value
    }
  }

  const clearFilters = (section) => {
    if (filters.value[section]) {
      Object.keys(filters.value[section]).forEach(key => {
        filters.value[section][key] = ''
      })
    }
  }

  const clearAllFilters = () => {
    Object.keys(filters.value).forEach(section => {
      clearFilters(section)
    })
  }

  // Actions - Pagination
  const setPagination = (section, data) => {
    if (pagination.value[section]) {
      pagination.value[section] = { ...pagination.value[section], ...data }
    }
  }

  const resetPagination = (section) => {
    if (pagination.value[section]) {
      pagination.value[section] = { page: 1, limit: 10, total: 0 }
    }
  }

  // Actions - Confirm Dialog
  const showConfirmDialog = (message, callback) => {
    modalData.value.confirmMessage = message
    modalData.value.confirmCallback = callback
    openModal('confirmAction')
  }

  const executeConfirmAction = () => {
    if (modalData.value.confirmCallback) {
      modalData.value.confirmCallback()
    }
    closeModal('confirmAction')
  }

  // Utility actions
  const showSuccess = (message) => {
    addNotification({
      type: 'success',
      title: 'Успіх',
      message
    })
  }

  const showError = (message) => {
    addNotification({
      type: 'error',
      title: 'Помилка',
      message
    })
  }

  const showWarning = (message) => {
    addNotification({
      type: 'warning',
      title: 'Попередження',
      message
    })
  }

  const showInfo = (message) => {
    addNotification({
      type: 'info',
      title: 'Інформація',
      message
    })
  }

  return {
    // State
    loading,
    sidebarCollapsed,
    darkMode,
    notifications,
    currentPage,
    breadcrumbs,
    modals,
    modalData,
    filters,
    pagination,

    // Getters
    isLoading,
    isSidebarCollapsed,
    isDarkMode,
    hasNotifications,
    unreadNotifications,

    // Actions
    setLoading,
    startLoading,
    stopLoading,
    toggleSidebar,
    setSidebarCollapsed,
    toggleDarkMode,
    initTheme,
    addNotification,
    removeNotification,
    markNotificationRead,
    clearAllNotifications,
    setCurrentPage,
    setBreadcrumbs,
    openModal,
    closeModal,
    closeAllModals,
    setFilter,
    clearFilters,
    clearAllFilters,
    setPagination,
    resetPagination,
    showConfirmDialog,
    executeConfirmAction,
    showSuccess,
    showError,
    showWarning,
    showInfo
  }
})
