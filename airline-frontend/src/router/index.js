
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

// Lazy loading components
const Login = () => import('./views/Login.vue')
const AdminDashboard = () => import('./views/AdminDashboard.vue')
const DispatcherDashboard = () => import('./views/DispatcherDashboard.vue')
const FlightManagement = () => import('./views/FlightManagement.vue')
const CrewManagement = () => import('./views/CrewManagement.vue')
const CrewAssignment = () => import('./views/CrewAssignment.vue')

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: (route) => {
      const authStore = useAuthStore()
      if (authStore.user?.role === 'ADMIN') {
        return AdminDashboard()
      } else {
        return DispatcherDashboard()
      }
    },
    meta: { requiresAuth: true }
  },
  {
    path: '/flights',
    name: 'Flights',
    component: FlightManagement,
    meta: { requiresAuth: true }
  },
  {
    path: '/crew',
    name: 'Crew',
    component: CrewManagement,
    meta: { requiresAuth: true }
  },
  {
    path: '/assignments',
    name: 'Assignments',
    component: CrewAssignment,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: AdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Wait for auth initialization if needed
  if (authStore.isLoading) {
    await authStore.initializeAuth()
  }

  const isAuthenticated = authStore.isAuthenticated
  const userRole = authStore.user?.role

  // Handle guest-only routes
  if (to.meta.requiresGuest && isAuthenticated) {
    return next('/dashboard')
  }

  // Handle auth-required routes
  if (to.meta.requiresAuth && !isAuthenticated) {
    return next('/login')
  }

  // Handle admin-only routes
  if (to.meta.requiresAdmin && userRole !== 'ADMIN') {
    return next('/dashboard')
  }

  next()
})

export default router
