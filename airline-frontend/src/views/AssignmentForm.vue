<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-lg font-semibold text-gray-900">
        {{ isEditing ? 'Редагувати призначення' : 'Призначити екіпаж' }}
      </h3>
      <button
        v-if="onClose"
        @click="onClose"
        class="text-gray-400 hover:text-gray-600"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>

    <form @submit.prevent="handleSubmit">
      <!-- Вибір рейсу -->
      <div class="mb-6" v-if="!selectedFlight">
        <label class="block text-sm font-medium text-gray-700 mb-2">Рейс</label>
        <select
          v-model="form.flight_id"
          @change="onFlightChange"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        >
          <option value="">Оберіть рейс</option>
          <option
            v-for="flight in availableFlights"
            :key="flight.id"
            :value="flight.id"
          >
            {{ flight.flight_number }} - {{ flight.departure_city }} → {{ flight.arrival_city }}
            ({{ formatDateTime(flight.departure_time) }})
          </option>
        </select>
      </div>

      <!-- Інформація про вибраний рейс -->
      <div v-if="currentFlight" class="mb-6 p-4 bg-blue-50 rounded-lg">
        <h4 class="font-medium text-blue-900 mb-2">Рейс {{ currentFlight.flight_number }}</h4>
        <div class="grid grid-cols-2 gap-4 text-sm text-blue-800">
          <div>
            <span class="font-medium">Маршрут:</span>
            {{ currentFlight.departure_city }} → {{ currentFlight.arrival_city }}
          </div>
          <div>
            <span class="font-medium">Відправлення:</span>
            {{ formatDateTime(currentFlight.departure_time) }}
          </div>
          <div>
            <span class="font-medium">Прибуття:</span>
            {{ formatDateTime(currentFlight.arrival_time) }}
          </div>
          <div>
            <span class="font-medium">Літак:</span>
            {{ currentFlight.aircraft_type }}
          </div>
        </div>
      </div>

      <!-- Автоматичне призначення -->
      <div v-if="currentFlight && !isEditing" class="mb-6">
        <div class="flex items-center justify-between">
          <h4 class="text-md font-medium text-gray-900">Екіпаж</h4>
          <button
            type="button"
            @click="autoAssignCrew"
            :disabled="autoAssigning"
            class="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-100 rounded-md hover:bg-blue-200 disabled:opacity-50"
          >
            {{ autoAssigning ? 'Призначення...' : 'Автопризначення' }}
          </button>
        </div>
        <p class="text-sm text-gray-600 mt-1">
          Оберіть членів екіпажу вручну або скористайтеся автоматичним призначенням
        </p>
      </div>

      <!-- Позиції екіпажу -->
      <div class="space-y-4">
        <div
          v-for="position in requiredPositions"
          :key="position.id"
          class="border border-gray-200 rounded-lg p-4"
        >
          <div class="flex items-center justify-between mb-3">
            <h5 class="font-medium text-gray-900">
              {{ getPositionName(position.position_name) }}
              <span v-if="position.is_required" class="text-red-500">*</span>
            </h5>
            <span class="text-sm text-gray-500">
              Призначено: {{ getAssignedCount(position.position_name) }}
            </span>
          </div>

          <!-- Вибрані члени екіпажу для цієї позиції -->
          <div v-if="getAssignedMembers(position.position_name).length > 0" class="mb-3">
            <div class="space-y-2">
              <div
                v-for="member in getAssignedMembers(position.position_name)"
                :key="member.id"
                class="flex items-center justify-between p-2 bg-green-50 rounded border border-green-200"
              >
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                    {{ member.first_name.charAt(0) }}{{ member.last_name.charAt(0) }}
                  </div>
                  <div>
                    <span class="font-medium text-green-900">
                      {{ member.first_name }} {{ member.last_name }}
                    </span>
                    <span class="text-sm text-green-700 ml-2">({{ member.employee_id }})</span>
                  </div>
                </div>
                <button
                  type="button"
                  @click="removeMember(member.id)"
                  class="text-red-500 hover:text-red-700"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Додавання нового члена екіпажу -->
          <div class="flex space-x-2">
            <select
              :value="selectedMemberForPosition[position.position_name] || ''"
              @change="(e) => selectedMemberForPosition[position.position_name] = e.target.value"
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Оберіть члена екіпажу</option>
              <option
                v-for="member in getAvailableMembersForPosition(position.position_name)"
                :key="member.id"
                :value="member.id"
              >
                {{ member.first_name }} {{ member.last_name }} ({{ member.employee_id }})
                - {{ getCertificationLevel(member.certification_level) }}
              </option>
            </select>
            <button
              type="button"
              @click="addMember(position.position_name)"
              :disabled="!selectedMemberForPosition[position.position_name]"
              class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Додати
            </button>
          </div>

          <!-- Рекомендації -->
          <div v-if="getRecommendations(position.position_name).length > 0" class="mt-3">
            <h6 class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
              Рекомендовані
            </h6>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="rec in getRecommendations(position.position_name)"
                :key="rec.id"
                type="button"
                @click="addRecommendedMember(rec, position.position_name)"
                class="px-3 py-1 text-xs font-medium text-blue-600 bg-blue-100 rounded-full hover:bg-blue-200"
              >
                {{ rec.first_name }} {{ rec.last_name }}
                <span class="text-blue-500">({{ rec.score }}%)</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Додаткові примітки -->
      <div class="mt-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">Примітки</label>
        <textarea
          v-model="form.notes"
          rows="3"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Додаткові примітки щодо призначення..."
        ></textarea>
      </div>

      <!-- Перевірки та попередження -->
      <div v-if="validationWarnings.length > 0" class="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h6 class="font-medium text-yellow-800 mb-2">Попередження:</h6>
        <ul class="list-disc list-inside space-y-1 text-sm text-yellow-700">
          <li v-for="warning in validationWarnings" :key="warning">{{ warning }}</li>
        </ul>
      </div>

      <div v-if="validationErrors.length > 0" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
        <h6 class="font-medium text-red-800 mb-2">Помилки:</h6>
        <ul class="list-disc list-inside space-y-1 text-sm text-red-700">
          <li v-for="error in validationErrors" :key="error">{{ error }}</li>
        </ul>
      </div>

      <!-- Кнопки дій -->
      <div class="flex justify-end space-x-3 mt-6 pt-6 border-t border-gray-200">
        <button
          v-if="onCancel"
          type="button"
          @click="onCancel"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
        >
          Скасувати
        </button>
        <button
          type="submit"
          :disabled="!canSubmit || submitting"
          class="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ submitting ? 'Збереження...' : (isEditing ? 'Оновити' : 'Призначити') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useFlightsStore } from '@/stores/flights'
import { useCrewStore } from '@/stores/crew'
import { useAssignmentsStore } from '@/stores/assignments'
import { formatDateTime } from '@/core/utils'

export default {
  name: 'AssignmentForm',
  props: {
    selectedFlight: {
      type: Object,
      default: null
    },
    existingAssignment: {
      type: Object,
      default: null
    },
    onClose: {
      type: Function,
      default: null
    },
    onCancel: {
      type: Function,
      default: null
    },
    onSuccess: {
      type: Function,
      default: null
    }
  },
  emits: ['submit', 'cancel', 'close'],
  setup(props, { emit }) {
    const flightsStore = useFlightsStore()
    const crewStore = useCrewStore()
    const assignmentsStore = useAssignmentsStore()

    const form = ref({
      flight_id: props.selectedFlight?.id || '',
      crew_assignments: [],
      notes: ''
    })

    const selectedMemberForPosition = ref({})
    const submitting = ref(false)
    const autoAssigning = ref(false)
    const availableCrewMembers = ref([])
    const recommendations = ref({})

    const isEditing = computed(() => !!props.existingAssignment)

    const availableFlights = computed(() => {
      return flightsStore.flights.filter(f => f.status === 'SCHEDULED')
    })

    const currentFlight = computed(() => {
      if (props.selectedFlight) return props.selectedFlight
      return flightsStore.flights.find(f => f.id === form.value.flight_id)
    })

    const requiredPositions = computed(() => crewStore.positions || [])

    const validationErrors = computed(() => {
      const errors = []

      if (!form.value.flight_id) {
        errors.push('Необхідно обрати рейс')
      }

      // Перевірка обов'язкових позицій
      const requiredPos = requiredPositions.value.filter(p => p.is_required)
      for (const pos of requiredPos) {
        const assigned = getAssignedCount(pos.position_name)
        if (assigned === 0) {
          errors.push(`Позиція "${getPositionName(pos.position_name)}" є обов'язковою`)
        }
      }

      return errors
    })

    const validationWarnings = computed(() => {
      const warnings = []

      if (!currentFlight.value) return warnings

      const totalRequired = currentFlight.value.crew_required || 4
      const totalAssigned = form.value.crew_assignments.length

      if (totalAssigned < totalRequired) {
        warnings.push(`Призначено ${totalAssigned} з ${totalRequired} необхідних членів екіпажу`)
      }

      return warnings
    })

    const canSubmit = computed(() => {
      return validationErrors.value.length === 0 && form.value.crew_assignments.length > 0
    })

    function getPositionName(position) {
      const map = {
        captain: 'Капітан',
        first_officer: 'Перший офіцер',
        flight_attendant: 'Стюард',
        engineer: 'Інженер',
      }
      return map[position] || position
    }

    function getCertificationLevel(level) {
      const levels = {
        1: 'Базовий',
        2: 'Середній',
        3: 'Просунутий'
      }
      return levels[level] || 'Невідомо'
    }

    function getAssignedMembers(positionName) {
      return form.value.crew_assignments.filter(m => m.position_name === positionName)
    }

    function getAssignedCount(positionName) {
      return getAssignedMembers(positionName).length
    }

    function getAvailableMembersForPosition(positionName) {
      const assignedIds = form.value.crew_assignments.map(m => m.id)
      return availableCrewMembers.value.filter(member =>
        member.position_name === positionName &&
        !assignedIds.includes(member.id)
    }

    function getRecommendations(positionName) {
      return recommendations.value[positionName] || []
    }

    function addMember(positionName) {
      const memberId = selectedMemberForPosition.value[positionName]
      if (!memberId) return
      const member = availableCrewMembers.value.find(m => m.id === memberId)
      if (member) {
        form.value.crew_assignments.push({ ...member, position_name: positionName })
        selectedMemberForPosition.value[positionName] = ''
      }
    }

    function addRecommendedMember(member, positionName) {
      if (!form.value.crew_assignments.find(m => m.id === member.id)) {
        form.value.crew_assignments.push({ ...member, position_name: positionName })
      }
    }

    function removeMember(memberId) {
      form.value.crew_assignments = form.value.crew_assignments.filter(m => m.id !== memberId)
    }

    async function autoAssignCrew() {
      if (!currentFlight.value) return
      autoAssigning.value = true
      try {
        const result = await assignmentsStore.autoAssignCrew(currentFlight.value.id)
        form.value.crew_assignments = result.assignments
        recommendations.value = result.recommendations || {}
      } catch (error) {
        console.error('Auto-assign error:', error)
      } finally {
        autoAssigning.value = false
      }
    }

    function onFlightChange() {
      form.value.crew_assignments = []
      recommendations.value = {}
      selectedMemberForPosition.value = {}
    }

    async function handleSubmit() {
      if (!canSubmit.value) return
      submitting.value = true
      try {
        if (isEditing.value && props.existingAssignment) {
          await assignmentsStore.updateAssignment(props.existingAssignment.id, form.value)
        } else {
          await assignmentsStore.createAssignment(form.value)
        }
        emit('submit')
        if (props.onSuccess) props.onSuccess()
      } catch (error) {
        console.error('Submit error:', error)
      } finally {
        submitting.value = false
      }
    }

    async function loadData() {
      await flightsStore.fetchFlights()
      await crewStore.fetchCrewMembers()
      availableCrewMembers.value = crewStore.members

      if (isEditing.value && props.existingAssignment) {
        form.value.flight_id = props.existingAssignment.flight_id
        form.value.notes = props.existingAssignment.notes
        form.value.crew_assignments = props.existingAssignment.crew_assignments || []
      }

      if (props.selectedFlight) {
        form.value.flight_id = props.selectedFlight.id
      }
    }

    onMounted(loadData)

    watch(() => props.selectedFlight, (newVal) => {
      if (newVal) {
        form.value.flight_id = newVal.id
      }
    })

    return {
      form,
      currentFlight,
      availableFlights,
      requiredPositions,
      selectedMemberForPosition,
      validationErrors,
      validationWarnings,
      canSubmit,
      submitting,
      autoAssigning,
      isEditing,
      getPositionName,
      getAssignedMembers,
      getAssignedCount,
      getAvailableMembersForPosition,
      getRecommendations,
      getCertificationLevel,
      addMember,
      removeMember,
      autoAssignCrew,
      addRecommendedMember,
      handleSubmit,
      onFlightChange,
      formatDateTime
    }
  }
}
</script>
