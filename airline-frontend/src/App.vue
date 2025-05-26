<template>
  <div id="app">
    <div v-if="isLoading" class="min-h-screen flex items-center justify-center bg-gray-50">
      <div class="text-center">
        <div class="animate-spin rounded-full h-32 w-32 border-b-2 border-airline-blue mx-auto"></div>
        <p class="mt-4 text-lg text-gray-600">Завантаження...</p>
      </div>
    </div>

    <div v-else-if="!isAuthenticated" class="min-h-screen bg-gray-50">
      <router-view />
    </div>

    <div v-else class="min-h-screen bg-gray-50">
      <!-- Navigation -->
      <nav class="bg-white shadow-lg border-b border-gray-200">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="flex justify-between h-16">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <h1 class="text-2xl font-bold text-airline-blue">
                  ✈️ Airline System
                </h1>
              </div>

              <div class="hidden md:ml-10 md:flex md:space-x-8">
                <router-link
                  v-for="item in navigationItems"
                  :key="item.name"
                  :to="item.to"
                  class="text-gray-700 hover:text-airline-blue px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  :class="{ 'text-airline-blue bg-blue-50': $route.path === item.to }"
                >
                  <component :is="item.icon" class="w-4 h-4 inline mr-2" />
                  {{ item.name }}
                </router-link>
              </div>
            </div>

            <div class="flex items-center space-x-4">
              <div class="text-sm text-gray-700">
                Вітаємо, <span class="font-medium">{{ user?.first_name }} {{ user?.last_name }}</span>
                <span class="text-xs bg-airline-blue text-white px-2 py-1 rounded-full ml-2">
                  {{ user?.role }}
                </span>
              </div>

              <button
                @click="logout"
                class="text-gray-700 hover:text-red-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                <LogOut class="w-4 h-4 inline mr-1" />
                Вийти
              </button>
            </div>
          </div>
        </div>
      </nav>

      <!-- Main Content -->
      <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import {
  Home,
  Plane,
  Users,
  Calendar,
  Settings,
  LogOut
} from 'lucide-vue-next'

export default {
  name: 'App',
  components: {
    Home,
    Plane,
    Users,
    Calendar,
    Settings,
    LogOut
  },
  setup() {
    const authStore = useAuthStore()
    const router = useRouter()
    const toast = useToast()

    const isLoading = computed(() => authStore.isLoading)
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    const user = computed(() => authStore.user)

    const navigationItems = computed(() => {
      const items = [
        { name: 'Головна', to: '/dashboard', icon: 'Home' },
        { name: 'Рейси', to: '/flights', icon: 'Plane' },
        { name: 'Екіпаж', to: '/crew', icon: 'Users' },
        { name: 'Призначення', to: '/assignments', icon: 'Calendar' }
      ]

      if (user.value?.role === 'ADMIN') {
        items.push({ name: 'Налаштування', to: '/admin', icon: 'Settings' })
      }

      return items
    })

    const logout = async () => {
      try {
        await authStore.logout()
        toast.success('Ви успішно вийшли з системи')
        router.push('/login')
      } catch (error) {
        toast.error('Помилка при виході з системи')
      }
    }

    onMounted(async () => {
      await authStore.initializeAuth()
    })

    return {
      isLoading,
      isAuthenticated,
      user,
      navigationItems,
      logout
    }
  }
}
</script>
