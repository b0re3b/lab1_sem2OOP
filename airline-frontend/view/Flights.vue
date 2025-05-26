<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Управління рейсами</h1>
      <button
        v-if="canManageFlights"
        @click="openCreateFlightModal"
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
        </svg>
        Додати рейс
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Дата</label>
          <input
            v-model="filters.date"
            type="date"
            class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Статус</label>
          <select
            v-model="filters.status"
            class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Всі статуси</option>
            <option value="SCHEDULED">Заплановано</option>
            <option value="DELAYED">Затримано</option>
            <option value="CANCELLED">Скасовано</option>
            <option value="COMPLETED">Завершено</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Місто вильоту</label>
          <input
            v-model="filters.departureCity"
            type="text"
            placeholder="Введіть місто"
            class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div class="flex items-end">
          <button
            @click="applyFilters"
            class="w-full bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md"
          >
            Застосувати
          </button>
        </div>
      </div>
    </div>

    <!-- Flights Table -->
    <div class="bg-white rounded-lg shadow-sm overflow-hidden">
      <DataTable
        :columns="flightColumns"
        :data="filteredFlights"
        :loading="loading"
        @row-click="handleFlightClick"
      >
        <template #status="{ value }">
          <span
            :class="getStatusClass(value)"
            class="px-2 py-1 text-xs font-medium rounded-full"
          >
            {{ getStatusText(value) }}
          </span>
        </template>
        <template #actions="{ row }">
          <div class="flex gap-2">
            <button
              @click.stop="openAssignCrewModal(row)"
              class="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Екіпаж
            </button>
            <button
              v-if="canManageFlights"
              @click.stop="editFlight(row)"
              class="text-green-600 hover:text-green-800 text-sm font-medium"
            >
              Редагувати
            </button>
            <button
              v-if="canManageFlights"
              @click.stop="deleteFlight(row)"
              class="text-red-600 hover:text-red-800 text-sm font-medium"
            >
              Видалити
            </button>
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Create/Edit Flight Modal -->
    <SimpleModal v-model:show="showFlightModal" title="Рейс" size="large">
      <form @submit.prevent="submitFlight" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Номер рейсу</label>
            <input
              v-model="flightForm.flight_number"
              type="text"
              required
              class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Тип літака</label>
            <select
              v-model="flightForm.aircraft_type"
              required
              class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Оберіть тип</option>
              <option value="Boeing 737">Boeing 737</option>
              <option value="Airbus A320">Airbus A320</option>
              <option value="Boeing 777">Boeing 777</option>
              <option value="Airbus A380">Airbus A380</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Місто вильоту</label>
            <input
              v-model="flightForm.departure_city"
              type="text"
              required
              class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Місто прибуття</label>
            <input
              v-model="flightForm.arrival_city"
              type="text"
              required
              class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Час вильоту</label>
            <input
              v-model="flightForm.departure_time"
              type="datetime-local"
              required
              class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Час прибуття</label>
            <input
              v-model="flightForm.arrival_time"
              type="datetime-local"
              required
              class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Кількість екіпажу</label>
            <input
              v-model.number="flightForm.crew_required"
              type="number"
              min="1"
              max="10"
              required
              class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div v-if="editingFlight">
            <label class="block text-sm font-medium text-gray-700 mb-1">Статус</label>
            <select
              v-model="flightForm.status"
              class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="SCHEDULED">Заплановано</option>
              <option value="DELAYED">Затримано</option>
              <option value="CANCELLED">Скасовано</option>
              <option value="COMPLETED">Завершено</option>
            </select>
          </div>
        </div>
        <div class="flex justify-end gap-3 pt-4">
          <button
            type="button"
            @click="showFlightModal = false"
            class="px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md"
          >
            Скасувати
          </button>
          <button
            type="submit"
            :disabled="submitting"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50"
          >
            {{ submitting ? 'Збереження...' : editingFlight ? 'Оновити' : 'Створити' }}
          </button>
        </div>
      </form>
    </SimpleModal>

    <!-- Assign Crew Modal -->
    <SimpleModal v-model:show="showCrewModal" title="Призначення екіпажу" size="large">
      <div v-if="selectedFlight">
        <div class="mb-4 p-4 bg-gray-50 rounded-lg">
          <h3 class="font-medium text-gray-900">{{ selectedFlight.flight_number }}</h3>
          <p class="text-sm text-gray-600">
            {{ selectedFlight.departure_city }} → {{ selectedFlight.arrival_city }}
          </p>
          <p class="text-sm text-gray-600">
            {{ formatDateTime(selectedFlight.departure_time) }} - {{ formatDateTime(selectedFlight.arrival_time) }}
          </p>
        </div>

        <!-- Current Assignments -->
        <div class="mb-6">
          <h4 class="font-medium text-gray-900 mb-3">Поточний екіпаж</h4>
          <div v-if="flightAssignments.length === 0" class="text-gray-500 text-sm">
            Екіпаж не призначено
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="assignment in flightAssignments"
              :key="assignment.id"
              class="flex justify-between items-center p-3 bg-green-50 rounded-lg"
            >
              <div>
                <div class="font-medium">{{ assignment.crew_member_name }}</div>
                <div class="text-sm text-gray-600">{{ assignment.position_name }}</div>
              </div>
              <button
                @click="removeAssignment(assignment.id)"
                class="text-red-600 hover:text-red-800 text-sm"
              >
                Видалити
              </button>
            </div>
          </div>
        </div>

        <!-- Available Crew -->
        <div>
          <h4 class="font-medium text-gray-900 mb-3">Доступний екіпаж</h4>
          <div class="space-y-2 max-h-64 overflow-y-auto">
            <div
              v-for="member in availableCrew"
              :key="member.id"
              class="flex justify-between items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <div>
                <div class="font-medium">{{ member.first_name }} {{ member.last_name }}</div>
                <div class="text-sm text-gray-600">{{ member.position_name }}</div>
                <div class="text-sm text-gray-500">{{ member.experience_years }} років досвіду</div>
              </div>
              <button
                @click="assignCrewMember(member.id)"
                class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
              >
                Призначити
              </button>
            </div>
          </div>
        </div>
      </div>
    </SimpleModal>
  </div>
</template>

<script>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDataStore } from '@/stores/data'
import { useAppStore } from '@/stores/app'
import DataTable from '@/components/DataTable.vue'
import SimpleModal from '@/components/SimpleModal.vue'
import { formatDateTime, showSuccess, showError } from '@/utils/helpers'
import { FLIGHT_STATUS } from '@/utils/constants'

export default {
  name: 'Flights',
  components: {
    DataTable,
    SimpleModal
  },
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const dataStore = useDataStore()
    const appStore = useAppStore()

    const loading = ref(false)
    const submitting = ref(false)
    const showFlightModal = ref(false)
    const showCrewModal = ref(false)
    const editingFlight = ref(null)
    const selectedFlight = ref(null)

    const filters = reactive({
      date: '',
      status: '',
      departureCity: ''
    })

    const flightForm = reactive({
      flight_number: '',
      departure_city: '',
      arrival_city: '',
      departure_time: '',
      arrival_time: '',
      aircraft_type: '',
      crew_required: 4,
      status: 'SCHEDULED'
    })

    const flightColumns = [
      { key: 'flight_number', label: 'Номер рейсу', sortable: true },
      { key: 'departure_city', label: 'Вільот' },
      { key: 'arrival_city', label: 'Прибуття' },
      { key: 'departure_time', label: 'Час вильоту', formatter: formatDateTime },
      { key: 'arrival_time', label: 'Час прибуття', formatter: formatDateTime },
      { key: 'aircraft_type', label: 'Літак' },
      { key: 'status', label: 'Статус', slot: true },
      { key: 'actions', label: 'Дії', slot: true, sortable: false }
    ]

    const canManageFlights = computed(() => {
      return authStore.user?.role === 'ADMIN'
    })

    const filteredFlights = computed(() => {
      let flights = dataStore.flights

      if (filters.date) {
        flights = flights.filter(flight =>
          flight.departure_time?.startsWith(filters.date)
        )
      }

      if (filters.status) {
        flights = flights.filter(flight => flight.status === filters.status)
      }

      if (filters.departureCity) {
        flights = flights.filter(flight =>
          flight.departure_city?.toLowerCase().includes(filters.departureCity.toLowerCase())
        )
      }

      return flights
    })

    const flightAssignments = computed(() => {
      if (!selectedFlight.value) return []
      return dataStore.assignments.filter(a => a.flight_id === selectedFlight.value.id)
    })

    const availableCrew = computed(() => {
      if (!selectedFlight.value) return []
      const assignedCrewIds = flightAssignments.value.map(a => a.crew_member_id)
      return dataStore.crew.filter(member =>
        member.is_available && !assignedCrewIds.includes(member.id)
      )
    })

    const loadData = async () => {
      loading.value = true
      try {
        await Promise.all([
          dataStore.fetchFlights(),
          dataStore.fetchCrew(),
          dataStore.fetchAssignments()
        ])
      } catch (error) {
        showError('Помилка завантаження даних')
      } finally {
        loading.value = false
      }
    }

    const applyFilters = () => {
      // Filters are applied automatically via computed property
    }

    const openCreateFlightModal = () => {
      editingFlight.value = null
      resetFlightForm()
      showFlightModal.value = true
    }

    const editFlight = (flight) => {
      editingFlight.value = flight
      Object.assign(flightForm, {
        ...flight,
        departure_time: formatDateTimeForInput(flight.departure_time),
        arrival_time: formatDateTimeForInput(flight.arrival_time)
      })
      showFlightModal.value = true
    }

    const submitFlight = async () => {
      submitting.value = true
      try {
        const flightData = {
          ...flightForm,
          departure_time: new Date(flightForm.departure_time).toISOString(),
          arrival_time: new Date(flightForm.arrival_time).toISOString()
        }

        if (editingFlight.value) {
          await dataStore.updateFlight(editingFlight.value.id, flightData)
          showSuccess('Рейс оновлено')
        } else {
          await dataStore.createFlight(flightData)
          showSuccess('Рейс створено')
        }

        showFlightModal.value = false
        await loadData()
      } catch (error) {
        showError('Помилка збереження рейсу')
      } finally {
        submitting.value = false
      }
    }

    const deleteFlight = async (flight) => {
      if (!confirm(`Ви впевнені, що хочете видалити рейс ${flight.flight_number}?`)) {
        return
      }

      try {
        await dataStore.deleteFlight(flight.id)
        showSuccess('Рейс видалено')
        await loadData()
      } catch (error) {
        showError('Помилка видалення рейсу')
      }
    }

    const openAssignCrewModal = async (flight) => {
      selectedFlight.value = flight
      showCrewModal.value = true
    }

    const assignCrewMember = async (crewMemberId) => {
      try {
        await dataStore.createAssignment({
          flight_id: selectedFlight.value.id,
          crew_member_id: crewMemberId
        })
        showSuccess('Екіпаж призначено')
        await dataStore.fetchAssignments()
      } catch (error) {
        showError('Помилка призначення екіпажу')
      }
    }

    const removeAssignment = async (assignmentId) => {
      try {
        await dataStore.deleteAssignment(assignmentId)
        showSuccess('Призначення скасовано')
        await dataStore.fetchAssignments()
      } catch (error) {
        showError('Помилка скасування призначення')
      }
    }

    const handleFlightClick = (flight) => {
      // Handle flight row click if needed
    }

    const resetFlightForm = () => {
      Object.assign(flightForm, {
        flight_number: '',
        departure_city: '',
        arrival_city: '',
        departure_time: '',
        arrival_time: '',
        aircraft_type: '',
        crew_required: 4,
        status: 'SCHEDULED'
      })
    }

    const formatDateTimeForInput = (dateTime) => {
      if (!dateTime) return ''
      return new Date(dateTime).toISOString().slice(0, 16)
    }

    const getStatusClass = (status) => {
      const classes = {
        SCHEDULED: 'bg-blue-100 text-blue-800',
        DELAYED: 'bg-yellow-100 text-yellow-800',
        CANCELLED: 'bg-red-100 text-red-800',
        COMPLETED: 'bg-green-100 text-green-800'
      }
      return classes[status] || 'bg-gray-100 text-gray-800'
    }

    const getStatusText = (status) => {
      return FLIGHT_STATUS[status] || status
    }

    onMounted(() => {
      loadData()
    })

    return {
      loading,
      submitting,
      showFlightModal,
      showCrewModal,
      editingFlight,
      selectedFlight,
      filters,
      flightForm,
      flightColumns,
      canManageFlights,
      filteredFlights,
      flightAssignments,
      availableCrew,
      applyFilters,
      openCreateFlightModal,
      editFlight,
      submitFlight,
      deleteFlight,
      openAssignCrewModal,
      assignCrewMember,
      removeAssignment,
      handleFlightClick,
      getStatusClass,
      getStatusText,
      formatDateTime
    }
  }
}
</script>
