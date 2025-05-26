<template>
  <div class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200">
    <div class="flex items-start justify-between mb-4">
      <div class="flex items-center space-x-3">
        <div class="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
          {{ initials }}
        </div>
        <div>
          <h3 class="text-lg font-semibold text-gray-900">
            {{ crewMember.first_name }} {{ crewMember.last_name }}
          </h3>
          <p class="text-sm text-gray-600">{{ crewMember.employee_id }}</p>
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <span
          :class="availabilityStatusClass"
          class="px-2 py-1 rounded-full text-xs font-medium"
        >
          {{ availabilityStatus }}
        </span>
        <div class="relative" v-if="showActions">
          <button
            @click="toggleActionsMenu"
            class="p-1 rounded-full hover:bg-gray-100 transition-colors"
          >
            <svg class="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/>
            </svg>
          </button>
          <div
            v-if="showActionsMenu"
            class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200"
          >
            <div class="py-1">
              <button
                @click="editCrewMember"
                class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                Редагувати
              </button>
              <button
                @click="toggleAvailability"
                class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                {{ crewMember.is_available ? 'Зробити недоступним' : 'Зробити доступним' }}
              </button>
              <button
                @click="viewAssignments"
                class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                Переглянути призначення
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4 mb-4">
      <div>
        <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Посада</label>
        <p class="text-sm font-medium text-gray-900">{{ positionName }}</p>
      </div>
      <div>
        <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Рівень</label>
        <p class="text-sm font-medium text-gray-900">{{ certificationLevel }}</p>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4 mb-4">
      <div>
        <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Досвід</label>
        <p class="text-sm font-medium text-gray-900">{{ crewMember.experience_years }} років</p>
      </div>
      <div v-if="crewMember.phone">
        <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Телефон</label>
        <p class="text-sm font-medium text-gray-900">{{ crewMember.phone }}</p>
      </div>
    </div>

    <div v-if="crewMember.email" class="mb-4">
      <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Email</label>
      <p class="text-sm font-medium text-gray-900">{{ crewMember.email }}</p>
    </div>

    <!-- Поточні призначення -->
    <div v-if="currentAssignments && currentAssignments.length > 0" class="mt-4 pt-4 border-t border-gray-200">
      <h4 class="text-sm font-medium text-gray-900 mb-2">Поточні призначення</h4>
      <div class="space-y-2">
        <div
          v-for="assignment in currentAssignments"
          :key="assignment.id"
          class="flex items-center justify-between p-2 bg-blue-50 rounded text-sm"
        >
          <span class="font-medium">{{ assignment.flight_number }}</span>
          <span class="text-gray-600">{{ formatDateTime(assignment.departure_time) }}</span>
        </div>
      </div>
    </div>

    <!-- Статистика навантаження -->
    <div v-if="workloadStats" class="mt-4 pt-4 border-t border-gray-200">
      <h4 class="text-sm font-medium text-gray-900 mb-2">Навантаження (цей місяць)</h4>
      <div class="flex items-center space-x-4 text-sm">
        <span class="text-gray-600">Рейсів: <span class="font-medium">{{ workloadStats.flights_count }}</span></span>
        <span class="text-gray-600">Годин: <span class="font-medium">{{ workloadStats.hours }}</span></span>
      </div>
    </div>

    <!-- Модальне вікно редагування -->
    <div v-if="showEditModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold mb-4">Редагувати члена екіпажу</h3>
        <form @submit.prevent="saveChanges">
          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Ім'я</label>
                <input
                  v-model="editForm.first_name"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Прізвище</label>
                <input
                  v-model="editForm.last_name"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Досвід (років)</label>
              <input
                v-model.number="editForm.experience_years"
                type="number"
                min="0"
                max="50"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Рівень сертифікації</label>
              <select
                v-model="editForm.certification_level"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="JUNIOR">Молодший</option>
                <option value="SENIOR">Старший</option>
                <option value="CAPTAIN">Капітан</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Телефон</label>
              <input
                v-model="editForm.phone"
                type="tel"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                v-model="editForm.email"
                type="email"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>
          </div>
          <div class="flex justify-end space-x-3 mt-6">
            <button
              type="button"
              @click="cancelEdit"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Скасувати
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {{ saving ? 'Збереження...' : 'Зберегти' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useCrewStore } from '@/stores/crew'
import { useAssignmentsStore } from '@/stores/assignments'
import { formatDateTime } from '@/core/utils'

export default {
  name: 'CrewMember',
  props: {
    crewMember: {
      type: Object,
      required: true
    },
    showActions: {
      type: Boolean,
      default: true
    },
    currentAssignments: {
      type: Array,
      default: () => []
    },
    workloadStats: {
      type: Object,
      default: null
    }
  },
  emits: ['edit', 'availability-changed', 'view-assignments'],
  setup(props, { emit }) {
    const crewStore = useCrewStore()
    const assignmentsStore = useAssignmentsStore()

    const showActionsMenu = ref(false)
    const showEditModal = ref(false)
    const saving = ref(false)
    const editForm = ref({})

    const initials = computed(() => {
      const first = props.crewMember.first_name?.charAt(0) || ''
      const last = props.crewMember.last_name?.charAt(0) || ''
      return (first + last).toUpperCase()
    })

    const availabilityStatus = computed(() => {
      return props.crewMember.is_available ? 'Доступний' : 'Недоступний'
    })

    const availabilityStatusClass = computed(() => {
      return props.crewMember.is_available
        ? 'bg-green-100 text-green-800'
        : 'bg-red-100 text-red-800'
    })

    const positionName = computed(() => {
      const positions = {
        'PILOT': 'Пілот',
        'CO_PILOT': 'Другий пілот',
        'NAVIGATOR': 'Штурман',
        'RADIO_OPERATOR': 'Радист',
        'FLIGHT_ATTENDANT': 'Стюард(еса)',
        'FLIGHT_ENGINEER': 'Бортінженер'
      }
      return positions[props.crewMember.position_name] || props.crewMember.position_name
    })

    const certificationLevel = computed(() => {
      const levels = {
        'JUNIOR': 'Молодший',
        'SENIOR': 'Старший',
        'CAPTAIN': 'Капітан'
      }
      return levels[props.crewMember.certification_level] || props.crewMember.certification_level
    })

    const toggleActionsMenu = () => {
      showActionsMenu.value = !showActionsMenu.value
    }

    const editCrewMember = () => {
      editForm.value = { ...props.crewMember }
      showEditModal.value = true
      showActionsMenu.value = false
    }

    const cancelEdit = () => {
      showEditModal.value = false
      editForm.value = {}
    }

    const saveChanges = async () => {
      try {
        saving.value = true
        await crewStore.updateCrewMember(props.crewMember.id, editForm.value)
        showEditModal.value = false
        emit('edit', editForm.value)
      } catch (error) {
        console.error('Помилка при збереженні:', error)
        alert('Помилка при збереженні змін')
      } finally {
        saving.value = false
      }
    }

    const toggleAvailability = async () => {
      try {
        await crewStore.setCrewAvailability(props.crewMember.id, !props.crewMember.is_available)
        emit('availability-changed', !props.crewMember.is_available)
        showActionsMenu.value = false
      } catch (error) {
        console.error('Помилка при зміні доступності:', error)
        alert('Помилка при зміні доступності')
      }
    }

    const viewAssignments = () => {
      emit('view-assignments', props.crewMember.id)
      showActionsMenu.value = false
    }

    const handleClickOutside = (event) => {
      if (!event.target.closest('.relative')) {
        showActionsMenu.value = false
      }
    }

    onMounted(() => {
      document.addEventListener('click', handleClickOutside)
    })

    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside)
    })

    return {
      showActionsMenu,
      showEditModal,
      saving,
      editForm,
      initials,
      availabilityStatus,
      availabilityStatusClass,
      positionName,
      certificationLevel,
      toggleActionsMenu,
      editCrewMember,
      cancelEdit,
      saveChanges,
      toggleAvailability,
      viewAssignments,
      formatDateTime
    }
  }
}
</script>
