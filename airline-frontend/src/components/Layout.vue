<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
      <div class="px-4 py-3 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <button @click="sidebarOpen = !sidebarOpen" class="lg:hidden p-1">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <h1 class="text-xl font-semibold">Система Авіакомпанії</h1>
        </div>

        <div class="flex items-center space-x-4">
          <span class="text-sm text-gray-600">{{ currentUser?.firstName }} {{ currentUser?.lastName }}</span>
          <span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">{{ userRole }}</span>
          <button @click="logout" class="text-sm text-red-600 hover:text-red-800">Вийти</button>
        </div>
      </div>
    </header>

    <div class="flex">
      <!-- Sidebar -->
      <aside
        class="fixed inset-y-0 left-0 z-50 w-64 bg-white border-r transform transition-transform lg:translate-x-0 lg:static lg:inset-0"
        :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
      >
        <div class="pt-16 lg:pt-4">ֳ
          <nav class="px-4 space-y-2">
            <router-link
              v-for="item in navigation"
              :key="item.path"
              :to="item.path"
              class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
              :class="$route.path === item.path
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:bg-gray-100'"
              @click="sidebarOpen = false"
            >
              <component :is="item.icon" class="w-5 h-5 mr-3" />
              {{ item.name }}
            </router-link>
          </nav>
        </div>
      </aside>

      <!-- Mobile overlay -->
      <div
        v-if="sidebarOpen"
        @click="sidebarOpen = false"
        class="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
      ></div>

      <!-- Main content -->
      <main class="flex-1 lg:ml-0">
        <div class="p-6">
          <router-view />
        </div>
      </main>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white p-4 rounded-lg">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-2 text-sm text-gray-600">Завантаження...</p>
      </div>
    </div>

    <!-- Notifications -->
    <div class="fixed top-4 right-4 z-40 space-y-2">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="bg-white border rounded-lg shadow-lg p-4 max-w-sm"
        :class="{
          'border-green-200 bg-green-50': notification.type === 'success',
          'border-red-200 bg-red-50': notification.type === 'error',
          'border-yellow-200 bg-yellow-50': notification.type === 'warning',
          'border-blue-200 bg-blue-50': notification.type === 'info'
        }"
      >
        <div class="flex justify-between items-start">
          <p class="text-sm font-medium">{{ notification.message }}</p>
          <button @click="removeNotification(notification.id)" class="ml-2 text-gray-400 hover:text-gray-600">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { NAVIGATION_ITEMS } from '@/config/navigation'

export default {
  name: 'SimpleLayout',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const appStore = useAppStore()

    const sidebarOpen = ref(false)

    const currentUser = computed(() => authStore.user)
    const userRole = computed(() => {
      switch (authStore.user?.role) {
        case 'ADMIN': return 'Адміністратор'
        case 'DISPATCHER': return 'Диспетчер'
        default: return 'Користувач'
      }
    })

    const navigation = computed(() => {
      return NAVIGATION_ITEMS.filter(item => {
        if (!item.roles) return true
        return item.roles.includes(authStore.user?.role)
      })
    })

    const isLoading = computed(() => appStore.isLoading)
    const notifications = computed(() => appStore.notifications)

    const logout = async () => {
      try {
        await authStore.logout()
        router.push('/login')
      } catch (error) {
        console.error('Logout error:', error)
      }
    }

    const removeNotification = (id) => {
      appStore.removeNotification(id)
    }

    return {
      sidebarOpen,
      currentUser,
      userRole,
      navigation,
      isLoading,
      notifications,
      logout,
      removeNotification
    }
  }
}
</script>
