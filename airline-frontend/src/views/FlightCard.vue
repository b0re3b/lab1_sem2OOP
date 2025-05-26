<template>
  <div class="bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow duration-200">
    <div class="p-6">
      <!-- Header with flight number and status -->
      <div class="flex justify-between items-start mb-4">
        <div>
          <h3 class="text-lg font-semibold text-gray-900">{{ flight.flight_number }}</h3>
          <p class="text-sm text-gray-600">{{ flight.aircraft_type }}</p>
        </div>
        <span
          :class="getStatusClass(flight.status)"
          class="px-3 py-1 rounded-full text-xs font-medium"
        >
          {{ formatStatus(flight.status) }}
        </span>
      </div>

      <!-- Route information -->
      <div class="flex items-center mb-4">
        <div class="flex-1">
          <p class="text-sm font-medium text-gray-900">{{ flight.departure_city }}</p>
          <p class="text-xs text-gray-500">{{ formatTime(flight.departure_time) }}</p>
        </div>

        <div class="mx-4 flex-shrink-0">
          <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
        </div>

        <div class="flex-1 text-right">
          <p class="text-sm font-medium text-gray-900">{{ flight.arrival_city }}</p>
          <p class="text-xs text-gray-500">{{ formatTime(flight.arrival_time) }}</p>
        </div>
      </div>

      <!-- Flight duration -->
      <div class="flex justify-center mb-4">
        <span class="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
          Duration: {{ calculateDuration(flight.departure_time, flight.arrival_time) }}
        </span>
      </div>

      <!-- Crew information -->
      <div class="border-t pt-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium text-gray-700">Crew Status</span>
          <span
            :class="getCrewStatusClass()"
            class="px-2 py-1 rounded text-xs font-medium"
          >
            {{ getCrewStatusText() }}
          </span>
        </div>

        <div class="flex items-center text-sm text-gray-600">
          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
          </svg>
          <span>{{ assignedCrewCount }} / {{ flight.crew_required || 4 }} assigned</span>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-2 mt-4 pt-4 border-t" v-if="showActions">
        <button
          @click="$emit('edit', flight)"
          class="flex-1 bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Edit
        </button>
        <button
          @click="$emit('assign-crew', flight)"
          class="flex-1 bg-green-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-green-700 transition-colors"
        >
          Assign Crew
        </button>
        <button
          @click="$emit('view-details', flight)"
          class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Details
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatDateTime, formatDuration } from '@/core/utils'

const props = defineProps({
  flight: {
    type: Object,
    required: true
  },
  assignedCrewCount: {
    type: Number,
    default: 0
  },
  showActions: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['edit', 'assign-crew', 'view-details'])

const getStatusClass = (status) => {
  const classes = {
    'SCHEDULED': 'bg-blue-100 text-blue-800',
    'DELAYED': 'bg-yellow-100 text-yellow-800',
    'CANCELLED': 'bg-red-100 text-red-800',
    'COMPLETED': 'bg-green-100 text-green-800'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

const formatStatus = (status) => {
  const statusMap = {
    'SCHEDULED': 'Scheduled',
    'DELAYED': 'Delayed',
    'CANCELLED': 'Cancelled',
    'COMPLETED': 'Completed'
  }
  return statusMap[status] || status
}

const formatTime = (dateTime) => {
  return formatDateTime(dateTime, 'HH:mm')
}

const calculateDuration = (departure, arrival) => {
  const start = new Date(departure)
  const end = new Date(arrival)
  const diffInMinutes = Math.round((end - start) / (1000 * 60))
  return formatDuration(diffInMinutes)
}

const getCrewStatusClass = () => {
  const required = props.flight.crew_required || 4
  const assigned = props.assignedCrewCount

  if (assigned === 0) return 'bg-red-100 text-red-800'
  if (assigned < required) return 'bg-yellow-100 text-yellow-800'
  return 'bg-green-100 text-green-800'
}

const getCrewStatusText = () => {
  const required = props.flight.crew_required || 4
  const assigned = props.assignedCrewCount

  if (assigned === 0) return 'Not Staffed'
  if (assigned < required) return 'Partially Staffed'
  return 'Fully Staffed'
}
</script>
