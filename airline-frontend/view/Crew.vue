<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold text-gray-900">Управління екіпажем</h1>
      <button
        @click="openCreateModal"
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        Додати члена екіпажу
      </button>
    </div>

    <!-- Фільтри -->
    <div class="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Посада</label>
          <select v-model="filters.position" @change="applyFilters" class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
            <option value="">Всі посади</option>
            <option v-for="position in positions" :key="position.id" :value="position.id">
              {{ position.position_name }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Рівень сертифікації</label>
          <select v-model="filters.certification" @change="applyFilters" class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
            <option value="">Всі рівні</option>
            <option value="JUNIOR">Junior</option>
            <option value="SENIOR">Senior</option>
            <option value="CAPTAIN">Captain</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Доступність</label>
          <select v-model="filters.availability" @change="applyFilters" class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
            <option value="">Всі</option>
            <option value="true">Доступні</option>
            <option value="false">Недоступні</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Пошук</label>
          <input
            v-model="filters.search"
            @input="applyFilters"
            type="text"
            placeholder="Пошук за ім'ям або ID"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
        </div>
      </div>
    </div>

    <!-- Таблиця екіпажу -->
    <DataTable
      :columns="tableColumns"
      :data="filteredCrew"
      :loading="loading"
      @edit="openEditModal"
      @delete="deleteMember"
      @toggle-availability="toggleAvailability"
    />

    <!-- Модальне вікно для створення/редагування -->
    <SimpleModal v-model="showModal" :title="modalTitle" size="lg">
      <form @submit.prevent="saveMember" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">ID співробітника *</label>
            <input
              v-model="form.employee_id"
              type="text"
              required
              :disabled="editMode"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Посада *</label>
            <select
              v-model="form.position_id"
              required
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="">Оберіть посаду</option>
              <option v-for="position in positions" :key="position.id" :value="position.id">
                {{ position.position_name }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Ім'я *</label>
            <input
              v-model="form.first_name"
              type="text"
              required
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Прізвище *</label>
            <input
              v-model="form.last_name"
              type="text"
              required
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Досвід (роки)</label>
            <input
              v-model.number="form.experience_years"
              type="number"
              min="0"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Рівень сертифікації</label>
            <select
              v-model="form.certification_level"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="JUNIOR">Junior</option>
              <option value="SENIOR">Senior</option>
              <option value="CAPTAIN">Captain</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Телефон</label>
            <input
              v-model="form.phone"
              type="tel"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              v-model="form.email"
              type="email"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
          </div>
        </div>
        <div class="flex items-center">
          <input
            v-model="form.is_available"
            type="checkbox"
            class="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
          <label class="ml-2 text-sm text-gray-700">Доступний для призначень</label>
        </div>
        <div class="flex justify-end gap-3 pt-4">
          <button
            type="button"
            @click="closeModal"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Скасувати
          </button>
          <button
            type="submit"
            :disabled="saving"
            class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {{ saving ? 'Збереження...' : 'Зберегти' }}
          </button>
        </div>
      </form>
    </SimpleModal>
  </div>
</template>

<script>
import { computed, onMounted, reactive, ref } from 'vue'
import { useDataStore } from '@/stores/data'
import { useAppStore } from '@/stores/app'
import DataTable from '@/components/DataTable.vue'
import SimpleModal from '@/components/SimpleModal.vue'
import { CERTIFICATION_LEVELS } from '@/utils/constants'

export default {
  name: 'CrewView',
  components: {
    DataTable,
    SimpleModal
  },
  setup() {
    const dataStore = useDataStore()
    const appStore = useAppStore()

    const loading = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    const editMode = ref(false)
    const currentMember = ref(null)

    const filters = reactive({
      position: '',
      certification: '',
      availability: '',
      search: ''
    })

    const form = reactive({
      employee_id: '',
      first_name: '',
      last_name: '',
      position_id: '',
      experience_years: 0,
      certification_level: 'JUNIOR',
      is_available: true,
      phone: '',
      email: ''
    })

    const tableColumns = [
      { key: 'employee_id', label: 'ID', sortable: true },
      { key: 'full_name', label: 'Ім\'я', sortable: true },
      { key: 'position_name', label: 'Посада', sortable: true },
      { key: 'experience_years', label: 'Досвід', sortable: true },
      { key: 'certification_level', label: 'Рівень', sortable: true },
      {
        key: 'is_available',
        label: 'Статус',
        type: 'badge',
        formatter: (value) => value ? { text: 'Доступний', class: 'bg-green-100 text-green-800' } : { text: 'Недоступний', class: 'bg-red-100 text-red-800' }
      },
      { key: 'actions', label: 'Дії', type: 'actions' }
    ]

    const crew = computed(() => dataStore.crew)
    const positions = computed(() => dataStore.positions)

    const filteredCrew = computed(() => {
      let result = crew.value

      if (filters.position) {
        result = result.filter(member => member.position_id == filters.position)
      }

      if (filters.certification) {
        result = result.filter(member => member.certification_level === filters.certification)
      }

      if (filters.availability !== '') {
        const isAvailable = filters.availability === 'true'
        result = result.filter(member => member.is_available === isAvailable)
      }

      if (filters.search) {
        const search = filters.search.toLowerCase()
        result = result.filter(member =>
          member.first_name.toLowerCase().includes(search) ||
          member.last_name.toLowerCase().includes(search) ||
          member.employee_id.toLowerCase().includes(search)
        )
      }

      return result.map(member => ({
        ...member,
        full_name: `${member.first_name} ${member.last_name}`,
        position_name: positions.value.find(p => p.id === member.position_id)?.position_name || 'Невідома'
      }))
    })

    const modalTitle = computed(() => editMode.value ? 'Редагувати члена екіпажу' : 'Додати члена екіпажу')

    const loadData = async () => {
      loading.value = true
      try {
        await Promise.all([
          dataStore.fetchCrew(),
          dataStore.fetchPositions()
        ])
      } catch (error) {
        appStore.showNotification('Помилка завантаження даних', 'error')
      } finally {
        loading.value = false
      }
    }

    const applyFilters = () => {
      // Фільтри застосовуються автоматично через computed
    }

    const openCreateModal = () => {
      editMode.value = false
      currentMember.value = null
      resetForm()
      showModal.value = true
    }

    const openEditModal = (member) => {
      editMode.value = true
      currentMember.value = member
      fillForm(member)
      showModal.value = true
    }

    const closeModal = () => {
      showModal.value = false
      resetForm()
    }

    const resetForm = () => {
      Object.assign(form, {
        employee_id: '',
        first_name: '',
        last_name: '',
        position_id: '',
        experience_years: 0,
        certification_level: 'JUNIOR',
        is_available: true,
        phone: '',
        email: ''
      })
    }

    const fillForm = (member) => {
      Object.assign(form, {
        employee_id: member.employee_id,
        first_name: member.first_name,
        last_name: member.last_name,
        position_id: member.position_id,
        experience_years: member.experience_years,
        certification_level: member.certification_level,
        is_available: member.is_available,
        phone: member.phone || '',
        email: member.email || ''
      })
    }

    const saveMember = async () => {
      saving.value = true
      try {
        if (editMode.value) {
          await dataStore.updateCrewMember(currentMember.value.id, form)
          appStore.showNotification('Член екіпажу оновлений успішно', 'success')
        } else {
          await dataStore.createCrewMember(form)
          appStore.showNotification('Член екіпажу створений успішно', 'success')
        }
        closeModal()
        await dataStore.fetchCrew()
      } catch (error) {
        appStore.showNotification('Помилка збереження', 'error')
      } finally {
        saving.value = false
      }
    }

    const deleteMember = async (member) => {
      if (!confirm(`Ви впевнені, що хочете видалити ${member.first_name} ${member.last_name}?`)) {
        return
      }

      try {
        await dataStore.deleteCrewMember(member.id)
        appStore.showNotification('Член екіпажу видалений успішно', 'success')
        await dataStore.fetchCrew()
      } catch (error) {
        appStore.showNotification('Помилка видалення', 'error')
      }
    }

    const toggleAvailability = async (member) => {
      try {
        await dataStore.updateCrewMember(member.id, {
          is_available: !member.is_available
        })
        appStore.showNotification('Статус доступності оновлений', 'success')
        await dataStore.fetchCrew()
      } catch (error) {
        appStore.showNotification('Помилка оновлення статусу', 'error')
      }
    }

    onMounted(() => {
      loadData()
    })

    return {
      loading,
      saving,
      showModal,
      editMode,
      filters,
      form,
      tableColumns,
      filteredCrew,
      positions,
      modalTitle,
      applyFilters,
      openCreateModal,
      openEditModal,
      closeModal,
      saveMember,
      deleteMember,
      toggleAvailability
    }
  }
}
</script>
