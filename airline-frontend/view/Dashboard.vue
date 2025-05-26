<template>
  <div class="dashboard">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">
        Панель управління - {{ userRoleTitle }}
      </h1>
      <p class="mt-2 text-gray-600">
        Вітаємо, {{ currentUser?.first_name }} {{ currentUser?.last_name }}
      </p>
    </div>

    <!-- Статистичні картки -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-6 w-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  Активні рейси
                </dt>
                <dd class="text-lg font-medium text-gray-900">
                  {{ stats.activeFlights }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
              </svg>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  Доступний екіпаж
                </dt>
                <dd class="text-lg font-medium text-gray-900">
                  {{ stats.availableCrew }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-6 w-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  Рейси потребують екіпаж
                </dt>
                <dd class="text-lg font-medium text-gray-900">
                  {{ stats.flightsNeedingCrew }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  Призначень сьогодні
                </dt>
                <dd class="text-lg font-medium text-gray-900">
                  {{ stats.todayAssignments }}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Швидкі дії -->
    <div class="bg-white shadow rounded-lg mb-8">
      <div class="px-4 py-5 sm:p-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Швидкі дії</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <router-link
            to="/flights"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
            </svg>
            Управління рейсами
          </router-link>

          <router-link
            to="/crew"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            <svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
            Управління екіпажем
          </router-link>

          <button
            @click="autoAssignCrew"
            :disabled="autoAssignLoading"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
            </svg>
            {{ autoAssignLoading ? 'Призначення...' : 'Автопризначення' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Таблиці з даними -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Найближчі рейси -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Найближчі рейси</h3>
          <div v-if="upcomingFlights.length === 0" class="text-gray-500 text-center py-4">
            Немає найближчих рейсів
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="flight in upcomingFlights"
              :key="flight.id"
              class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div>
                <div class="font-medium text-gray-900">{{ flight.flight_number }}</div>
                <div class="text-sm text-gray-500">
                  {{ flight.departure_city }} → {{ flight.arrival_city }}
                </div>
                <div class="text-xs text-gray-400">
                  {{ formatDateTime(flight.departure_time) }}
                </div>
              </div>
              <div class="text-right">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      :class="getStatusClass(flight.status)">
                  {{ getStatusText(flight.status) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Останні призначення -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Останні призначення</h3>
          <div v-if="recentAssignments.length === 0" class="text-gray-500 text-center py-4">
            Немає останніх призначень
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="assignment in recentAssignments"
              :key="assignment.id"
              class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div>
                <div class="font-medium text-gray-900">{{ assignment.flight_number }}</div>
                <div class="text-sm text-gray-500">
                  {{ assignment.crew_member_name }}
                </div>
                <div class="text-xs text-gray-400">
                  {{ formatDateTime(assignment.assigned_at) }}
                </div>
              </div>
              <div class="text-right">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      :class="getAssignmentStatusClass(assignment.status)">
                  {{ getAssignmentStatusText(assignment.status) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useDataStore } from '@/stores/data'
import { formatDateTime } from '@/utils/helpers'
import { FLIGHT_STATUS, ASSIGNMENT_STATUS } from '@/utils/constants'

export default {
  name: 'Dashboard',
  setup() {
    const authStore = useAuthStore()
    const dataStore = useDataStore()

    const autoAssignLoading = ref(false)

    const currentUser = computed(() => authStore.user)
    const userRoleTitle = computed(() => {
      return currentUser.value?.role === 'ADMIN' ? 'Адміністратор' : 'Диспетчер'
    })

    const stats = computed(() => ({
      activeFlights: dataStore.flights.filter(f => f.status === 'SCHEDULED').length,
      availableCrew: dataStore.crewMembers.filter(c => c.is_available).length,
      flightsNeedingCrew: dataStore.flights.filter(f =>
        f.status === 'SCHEDULED' &&
        dataStore.getFlightAssignments(f.id).length < f.crew_required
      ).length,
      todayAssignments: dataStore.assignments.filter(a => {
        const today = new Date()
        const assignedDate = new Date(a.assigned_at)
        return assignedDate.toDateString() === today.toDateString()
      }).length
    }))

    const upcomingFlights = computed(() => {
      const now = new Date()
      return dataStore.flights
        .filter(f => new Date(f.departure_time) > now)
        .sort((a, b) => new Date(a.departure_time) - new Date(b.departure_time))
        .slice(0, 5)
    })

    const recentAssignments = computed(() => {
      return dataStore.assignments
        .sort((a, b) => new Date(b.assigned_at) - new Date(a.assigned_at))
        .slice(0, 5)
        .map(assignment => {
          const flight = dataStore.flights.find(f => f.id === assignment.flight_id)
          const crewMember = dataStore.crewMembers.find(c => c.id === assignment.crew_member_id)
          return {
            ...assignment,
            flight_number: flight?.flight_number || 'N/A',
            crew_member_name: crewMember ? `${crewMember.first_name} ${crewMember.last_name}` : 'N/A'
          }
        })
    })

    const getStatusClass = (status) => {
      const classes = {
        'SCHEDULED': 'bg-blue-100 text-blue-800',
        'DELAYED': 'bg-yellow-100 text-yellow-800',
        'CANCELLED': 'bg-red-100 text-red-800',
        'COMPLETED': 'bg-green-100 text-green-800'
      }
      return classes[status] || 'bg-gray-100 text-gray-800'
    }

    const getStatusText = (status) => {
      return FLIGHT_STATUS[status] || status
    }

    const getAssignmentStatusClass = (status) => {
      const classes = {
        'ASSIGNED': 'bg-blue-100 text-blue-800',
        'CONFIRMED': 'bg-green-100 text-green-800',
        'CANCELLED': 'bg-red-100 text-red-800'
      }
      return classes[status] || 'bg-gray-100 text-gray-800'
    }

    const getAssignmentStatusText = (status) => {
      return ASSIGNMENT_STATUS[status] || status
    }

    const autoAssignCrew = async () => {
      try {
        autoAssignLoading.value = true
        await dataStore.autoAssignCrew()
        // Оновлюємо дані після автопризначення
        await loadDashboardData()
      } catch (error) {
        console.error('Помилка автопризначення:', error)
      } finally {
        autoAssignLoading.value = false
      }
    }

    const loadDashboardData = async () => {
      try {
        await Promise.all([
          dataStore.loadFlights(),
          dataStore.loadCrewMembers(),
          dataStore.loadAssignments()
        ])
      } catch (error) {
        console.error('Помилка завантаження даних панелі:', error)
      }
    }

    onMounted(() => {
      loadDashboardData()
    })

    return {
      currentUser,
      userRoleTitle,
      stats,
      upcomingFlights,
      recentAssignments,
      autoAssignLoading,
      autoAssignCrew,
      formatDateTime,
      getStatusClass,
      getStatusText,
      getAssignmentStatusClass,
      getAssignmentStatusText
    }
  }
}
</script>
