<template>
  <div class="bg-white rounded-lg shadow">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900">{{ title }}</h3>
        <div class="flex items-center space-x-3">
          <!-- Search -->
          <div class="relative" v-if="searchable">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Пошук..."
              class="pl-8 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
            <svg class="absolute left-2 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          <!-- Add Button -->
          <button
            v-if="canAdd"
            @click="$emit('add')"
            class="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            {{ addButtonText }}
          </button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              @click="column.sortable && sort(column.key)"
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              :class="column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''"
            >
              <div class="flex items-center space-x-1">
                <span>{{ column.label }}</span>
                <div v-if="column.sortable" class="flex flex-col">
                  <svg
                    class="w-3 h-3"
                    :class="sortBy === column.key && sortOrder === 'asc' ? 'text-blue-600' : 'text-gray-400'"
                    fill="currentColor" viewBox="0 0 20 20"
                  >
                    <path fill-rule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clip-rule="evenodd" />
                  </svg>
                  <svg
                    class="w-3 h-3 -mt-1"
                    :class="sortBy === column.key && sortOrder === 'desc' ? 'text-blue-600' : 'text-gray-400'"
                    fill="currentColor" viewBox="0 0 20 20"
                  >
                    <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                  </svg>
                </div>
              </div>
            </th>
            <th v-if="actions.length > 0" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Дії
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="loading" class="text-center">
            <td :colspan="columns.length + (actions.length > 0 ? 1 : 0)" class="px-6 py-4">
              <div class="flex items-center justify-center">
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span class="ml-2 text-sm text-gray-500">Завантаження...</span>
              </div>
            </td>
          </tr>
          <tr v-else-if="filteredData.length === 0" class="text-center">
            <td :colspan="columns.length + (actions.length > 0 ? 1 : 0)" class="px-6 py-8 text-sm text-gray-500">
              {{ emptyMessage }}
            </td>
          </tr>
          <tr
            v-else
            v-for="(item, index) in paginatedData"
            :key="item.id || index"
            class="hover:bg-gray-50"
          >
            <td
              v-for="column in columns"
              :key="column.key"
              class="px-6 py-4 whitespace-nowrap text-sm"
              :class="column.class || 'text-gray-900'"
            >
              <!-- Custom slot content -->
              <slot
                v-if="$slots[`cell-${column.key}`]"
                :name="`cell-${column.key}`"
                :item="item"
                :value="getNestedValue(item, column.key)"
              ></slot>

              <!-- Status badges -->
              <span
                v-else-if="column.type === 'status'"
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="getStatusClass(getNestedValue(item, column.key))"
              >
                {{ getStatusText(getNestedValue(item, column.key)) }}
              </span>

              <!-- Dates -->
              <span v-else-if="column.type === 'date'">
                {{ formatDate(getNestedValue(item, column.key)) }}
              </span>

              <!-- DateTime -->
              <span v-else-if="column.type === 'datetime'">
                {{ formatDateTime(getNestedValue(item, column.key)) }}
              </span>

              <!-- Boolean -->
              <span v-else-if="column.type === 'boolean'">
                <span
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                  :class="getNestedValue(item, column.key) ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                >
                  {{ getNestedValue(item, column.key) ? 'Так' : 'Ні' }}
                </span>
              </span>

              <!-- Default text -->
              <span v-else>
                {{ getNestedValue(item, column.key) || '-' }}
              </span>
            </td>

            <!-- Actions -->
            <td v-if="actions.length > 0" class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <div class="flex items-center justify-end space-x-2">
                <button
                  v-for="action in actions"
                  :key="action.name"
                  @click="$emit(action.event, item)"
                  :class="action.class || 'text-blue-600 hover:text-blue-900'"
                  class="font-medium transition-colors"
                  :title="action.title"
                >
                  {{ action.label }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
      <div class="flex items-center justify-between">
        <div class="flex-1 flex justify-between sm:hidden">
          <button
            @click="currentPage > 1 && (currentPage--)"
            :disabled="currentPage === 1"
            class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Попередня
          </button>
          <button
            @click="currentPage < totalPages && (currentPage++)"
            :disabled="currentPage === totalPages"
            class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Наступна
          </button>
        </div>
        <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
          <div>
            <p class="text-sm text-gray-700">
              Показано <span class="font-medium">{{ startIndex }}</span> до <span class="font-medium">{{ endIndex }}</span> з <span class="font-medium">{{ filteredData.length }}</span> записів
            </p>
          </div>
          <div>
            <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
              <button
                @click="currentPage > 1 && (currentPage--)"
                :disabled="currentPage === 1"
                class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ‹
              </button>
              <button
                v-for="page in visiblePages"
                :key="page"
                @click="currentPage = page"
                :class="page === currentPage
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-500 border-gray-300 hover:bg-gray-50'"
                class="relative inline-flex items-center px-4 py-2 border text-sm font-medium"
              >
                {{ page }}
              </button>
              <button
                @click="currentPage < totalPages && (currentPage++)"
                :disabled="currentPage === totalPages"
                class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ›
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { formatDate, formatDateTime, getStatusClass, getStatusText } from '@/utils/helpers'

export default {
  name: 'DataTable',
  props: {
    title: {
      type: String,
      default: 'Таблиця'
    },
    data: {
      type: Array,
      default: () => []
    },
    columns: {
      type: Array,
      required: true
    },
    actions: {
      type: Array,
      default: () => []
    },
    searchable: {
      type: Boolean,
      default: true
    },
    canAdd: {
      type: Boolean,
      default: false
    },
    addButtonText: {
      type: String,
      default: 'Додати'
    },
    loading: {
      type: Boolean,
      default: false
    },
    emptyMessage: {
      type: String,
      default: 'Немає даних для відображення'
    },
    pageSize: {
      type: Number,
      default: 10
    }
  },
  emits: ['add', 'edit', 'delete', 'view', 'assign'],
  setup(props) {
    const searchQuery = ref('')
    const sortBy = ref('')
    const sortOrder = ref('asc')
    const currentPage = ref(1)

    // Filtered data based on search
    const filteredData = computed(() => {
      if (!searchQuery.value) return props.data

      const query = searchQuery.value.toLowerCase()
      return props.data.filter(item => {
        return props.columns.some(column => {
          const value = getNestedValue(item, column.key)
          return value && value.toString().toLowerCase().includes(query)
        })
      })
    })

    // Sorted data
    const sortedData = computed(() => {
      if (!sortBy.value) return filteredData.value

      return [...filteredData.value].sort((a, b) => {
        const aVal = getNestedValue(a, sortBy.value)
        const bVal = getNestedValue(b, sortBy.value)

        if (aVal === bVal) return 0

        const result = aVal > bVal ? 1 : -1
        return sortOrder.value === 'asc' ? result : -result
      })
    })

    // Pagination
    const totalPages = computed(() => Math.ceil(sortedData.value.length / props.pageSize))
    const startIndex = computed(() => (currentPage.value - 1) * props.pageSize + 1)
    const endIndex = computed(() => Math.min(currentPage.value * props.pageSize, sortedData.value.length))

    const paginatedData = computed(() => {
      const start = (currentPage.value - 1) * props.pageSize
      return sortedData.value.slice(start, start + props.pageSize)
    })

    const visiblePages = computed(() => {
      const pages = []
      const total = totalPages.value
      const current = currentPage.value

      if (total <= 7) {
        for (let i = 1; i <= total; i++) {
          pages.push(i)
        }
      } else {
        if (current <= 4) {
          for (let i = 1; i <= 5; i++) {
            pages.push(i)
          }
          pages.push('...', total)
        } else if (current >= total - 3) {
          pages.push(1, '...')
          for (let i = total - 4; i <= total; i++) {
            pages.push(i)
          }
        } else {
          pages.push(1, '...', current - 1, current, current + 1, '...', total)
        }
      }

      return pages.filter(page => page !== '...' || pages.indexOf(page) !== pages.lastIndexOf(page))
    })

    // Helper function to get nested object values
    const getNestedValue = (obj, path) => {
      return path.split('.').reduce((value, key) => value?.[key], obj)
    }

    // Sorting
    const sort = (column) => {
      if (sortBy.value === column) {
        sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
      } else {
        sortBy.value = column
        sortOrder.value = 'asc'
      }
    }

    // Reset page when search changes
    watch(searchQuery, () => {
      currentPage.value = 1
    })

    // Reset page when data changes
    watch(() => props.data, () => {
      currentPage.value = 1
    })

    return {
      searchQuery,
      sortBy,
      sortOrder,
      currentPage,
      filteredData,
      paginatedData,
      totalPages,
      startIndex,
      endIndex,
      visiblePages,
      getNestedValue,
      sort,
      formatDate,
      formatDateTime,
      getStatusClass,
      getStatusText
    }
  }
}
</script>
