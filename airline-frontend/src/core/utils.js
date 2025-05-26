import { format, parseISO, isValid, addHours, differenceInMinutes } from 'date-fns'
import { uk } from 'date-fns/locale'

/**
 * Date and time utilities
 */
export const dateUtils = {
  /**
   * Format date to readable string
   */
  formatDate(date, formatStr = 'dd.MM.yyyy') {
    if (!date) return ''

    const parsedDate = typeof date === 'string' ? parseISO(date) : date
    if (!isValid(parsedDate)) return ''

    return format(parsedDate, formatStr, { locale: uk })
  },

  /**
   * Format date and time
   */
  formatDateTime(date, formatStr = 'dd.MM.yyyy HH:mm') {
    return this.formatDate(date, formatStr)
  },

  /**
   * Format time only
   */
  formatTime(date, formatStr = 'HH:mm') {
    return this.formatDate(date, formatStr)
  },

  /**
   * Get flight duration in minutes
   */
  getFlightDuration(departureTime, arrivalTime) {
    if (!departureTime || !arrivalTime) return 0

    const departure = typeof departureTime === 'string' ? parseISO(departureTime) : departureTime
    const arrival = typeof arrivalTime === 'string' ? parseISO(arrivalTime) : arrivalTime

    return differenceInMinutes(arrival, departure)
  },

  /**
   * Format duration in human readable format
   */
  formatDuration(minutes) {
    if (!minutes || minutes < 0) return '0 хв'

    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60

    if (hours === 0) return `${mins} хв`
    if (mins === 0) return `${hours} год`

    return `${hours} год ${mins} хв`
  },

  /**
   * Check if date is today
   */
  isToday(date) {
    if (!date) return false

    const parsedDate = typeof date === 'string' ? parseISO(date) : date
    const today = new Date()

    return parsedDate.toDateString() === today.toDateString()
  },

  /**
   * Get relative time (e.g., "через 2 години", "1 година тому")
   */
  getRelativeTime(date) {
    if (!date) return ''

    const parsedDate = typeof date === 'string' ? parseISO(date) : date
    const now = new Date()
    const diffMinutes = differenceInMinutes(parsedDate, now)

    if (Math.abs(diffMinutes) < 1) return 'зараз'

    if (diffMinutes > 0) {
      // Future
      if (diffMinutes < 60) return `через ${diffMinutes} хв`
      const hours = Math.floor(diffMinutes / 60)
      if (hours < 24) return `через ${hours} год`
      const days = Math.floor(hours / 24)
      return `через ${days} д`
    } else {
      // Past
      const absDiffMinutes = Math.abs(diffMinutes)
      if (absDiffMinutes < 60) return `${absDiffMinutes} хв тому`
      const hours = Math.floor(absDiffMinutes / 60)
      if (hours < 24) return `${hours} год тому`
      const days = Math.floor(hours / 24)
      return `${days} д тому`
    }
  }
}

/**
 * String utilities
 */
export const stringUtils = {
  /**
   * Capitalize first letter
   */
  capitalize(str) {
    if (!str) return ''
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
  },

  /**
   * Get initials from full name
   */
  getInitials(firstName, lastName) {
    const first = firstName ? firstName.charAt(0).toUpperCase() : ''
    const last = lastName ? lastName.charAt(0).toUpperCase() : ''
    return first + last
  },

  /**
   * Truncate string with ellipsis
   */
  truncate(str, length = 50) {
    if (!str || str.length <= length) return str
    return str.substring(0, length) + '...'
  },

  /**
   * Generate random string
   */
  generateId(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    let result = ''
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  }
}

/**
 * Validation utilities
 */
export const validators = {
  /**
   * Validate email
   */
  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  },

  /**
   * Validate phone number (Ukrainian format)
   */
  isValidPhone(phone) {
    const phoneRegex = /^\+380\d{9}$/
    return phoneRegex.test(phone)
  },

  /**
   * Validate flight number
   */
  isValidFlightNumber(flightNumber) {
    const flightRegex = /^[A-Z]{2}\d{3,4}$/
    return flightRegex.test(flightNumber)
  },

  /**
   * Validate employee ID
   */
  isValidEmployeeId(employeeId) {
    const employeeRegex = /^[A-Z]{1,2}\d{3}$/
    return employeeRegex.test(employeeId)
  },

  /**
   * Check if required field is filled
   */
  isRequired(value) {
    return value !== null && value !== undefined && value !== ''
  }
}

/**
 * Array utilities
 */
export const arrayUtils = {
  /**
   * Group array by key
   */
  groupBy(array, key) {
    return array.reduce((groups, item) => {
      const group = item[key]
      groups[group] = groups[group] || []
      groups[group].push(item)
      return groups
    }, {})
  },

  /**
   * Sort array by multiple keys
   */
  sortBy(array, ...keys) {
    return array.sort((a, b) => {
      for (const key of keys) {
        const aVal = a[key]
        const bVal = b[key]

        if (aVal < bVal) return -1
        if (aVal > bVal) return 1
      }
      return 0
    })
  },

  /**
   * Remove duplicates from array
   */
  unique(array, key = null) {
    if (!key) {
      return [...new Set(array)]
    }

    const seen = new Set()
    return array.filter(item => {
      const value = item[key]
      if (seen.has(value)) {
        return false
      }
      seen.add(value)
      return true
    })
  }
}

/**
 * Local storage utilities
 */
export const storageUtils = {
  /**
   * Set item in localStorage
   */
  setItem(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error('Error saving to localStorage:', error)
    }
  },

  /**
   * Get item from localStorage
   */
  getItem(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch (error) {
      console.error('Error reading from localStorage:', error)
      return defaultValue
    }
  },

  /**
   * Remove item from localStorage
   */
  removeItem(key) {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error('Error removing from localStorage:', error)
    }
  },

  /**
   * Clear all localStorage
   */
  clear() {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('Error clearing localStorage:', error)
    }
  }
}

/**
 * Error handling utilities
 */
export const errorUtils = {
  /**
   * Extract error message from API response
   */
  getErrorMessage(error) {
    if (typeof error === 'string') return error

    if (error.response?.data?.message) {
      return error.response.data.message
    }

    if (error.response?.data?.detail) {
      return error.response.data.detail
    }

    if (error.message) {
      return error.message
    }

    return 'Виникла невідома помилка'
  },

  /**
   * Check if error is authentication related
   */
  isAuthError(error) {
    return error.response?.status === 401 || error.response?.status === 403
  },

  /**
   * Check if error is network related
   */
  isNetworkError(error) {
    return !error.response || error.code === 'NETWORK_ERROR'
  }
}

/**
 * Flight status utilities
 */
export const flightUtils = {
  /**
   * Get flight status color
   */
  getStatusColor(status) {
    const colors = {
      SCHEDULED: 'blue',
      DELAYED: 'yellow',
      CANCELLED: 'red',
      COMPLETED: 'green'
    }
    return colors[status] || 'gray'
  },

  /**
   * Get flight status text in Ukrainian
   */
  getStatusText(status) {
    const texts = {
      SCHEDULED: 'Заплановано',
      DELAYED: 'Затримано',
      CANCELLED: 'Скасовано',
      COMPLETED: 'Завершено'
    }
    return texts[status] || status
  },

  /**
   * Get assignment status text
   */
  getAssignmentStatusText(status) {
    const texts = {
      ASSIGNED: 'Призначено',
      CONFIRMED: 'Підтверджено',
      CANCELLED: 'Скасовано'
    }
    return texts[status] || status
  }
}

/**
 * Permission utilities
 */
export const permissionUtils = {
  /**
   * Check if user can edit flights
   */
  canEditFlights(userRole) {
    return userRole === 'ADMIN'
  },

  /**
   * Check if user can manage crew
   */
  canManageCrew(userRole) {
    return ['ADMIN', 'DISPATCHER'].includes(userRole)
  },

  /**
   * Check if user can view all data
   */
  canViewAll(userRole) {
    return userRole === 'ADMIN'
  }
}

/**
 * Debounce function
 */
export function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * Deep clone object
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj.getTime())
  if (obj instanceof Array) return obj.map(item => deepClone(item))
  if (typeof obj === 'object') {
    const cloned = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        cloned[key] = deepClone(obj[key])
      }
    }
    return cloned
  }
}

/**
 * Format currency (if needed for future features)
 */
export function formatCurrency(amount, currency = 'UAH') {
  return new Intl.NumberFormat('uk-UA', {
    style: 'currency',
    currency: currency
  }).format(amount)
}
