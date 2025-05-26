/**
 * Конфігурація навігаційного меню
 * Містить структуру меню для різних ролей користувачів
 */

import {
  HomeIcon,
  AirplaneIcon,
  UsersIcon,
  ClipboardDocumentListIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  CalendarDaysIcon,
  UserGroupIcon
} from '@heroicons/vue/24/outline'

// Базові пункти меню доступні для всіх авторизованих користувачів
const baseMenuItems = [
  {
    id: 'dashboard',
    name: 'Головна',
    path: '/dashboard',
    icon: HomeIcon,
    roles: ['ADMIN', 'DISPATCHER'],
    description: 'Головна панель управління'
  }
]

// Меню для адміністратора
const adminMenuItems = [
  {
    id: 'flights',
    name: 'Рейси',
    path: '/flights',
    icon: AirplaneIcon,
    roles: ['ADMIN'],
    description: 'Управління рейсами',
    subItems: [
      {
        id: 'flights-list',
        name: 'Список рейсів',
        path: '/flights',
        description: 'Перегляд та редагування рейсів'
      },
      {
        id: 'flights-schedule',
        name: 'Розклад',
        path: '/flights/schedule',
        description: 'Розклад рейсів'
      }
    ]
  },
  {
    id: 'crew',
    name: 'Екіпаж',
    path: '/crew',
    icon: UsersIcon,
    roles: ['ADMIN'],
    description: 'Управління екіпажем',
    subItems: [
      {
        id: 'crew-list',
        name: 'Список екіпажу',
        path: '/crew',
        description: 'Перегляд та редагування даних екіпажу'
      },
      {
        id: 'crew-positions',
        name: 'Посади',
        path: '/crew/positions',
        description: 'Управління посадами екіпажу'
      }
    ]
  },
  {
    id: 'assignments',
    name: 'Призначення',
    path: '/assignments',
    icon: ClipboardDocumentListIcon,
    roles: ['ADMIN'],
    description: 'Призначення екіпажу на рейси'
  },
  {
    id: 'analytics',
    name: 'Аналітика',
    path: '/analytics',
    icon: ChartBarIcon,
    roles: ['ADMIN'],
    description: 'Звіти та аналітика',
    subItems: [
      {
        id: 'analytics-flights',
        name: 'Звіт по рейсах',
        path: '/analytics/flights',
        description: 'Статистика рейсів'
      },
      {
        id: 'analytics-crew',
        name: 'Звіт по екіпажу',
        path: '/analytics/crew',
        description: 'Статистика використання екіпажу'
      }
    ]
  },
  {
    id: 'users',
    name: 'Користувачі',
    path: '/users',
    icon: UserGroupIcon,
    roles: ['ADMIN'],
    description: 'Управління користувачами системи'
  },
  {
    id: 'settings',
    name: 'Налаштування',
    path: '/settings',
    icon: Cog6ToothIcon,
    roles: ['ADMIN'],
    description: 'Налаштування системи'
  }
]

// Меню для диспетчера
const dispatcherMenuItems = [
  {
    id: 'flights-view',
    name: 'Рейси',
    path: '/flights',
    icon: AirplaneIcon,
    roles: ['DISPATCHER'],
    description: 'Перегляд рейсів'
  },
  {
    id: 'crew-assignments',
    name: 'Призначення екіпажу',
    path: '/assignments',
    icon: ClipboardDocumentListIcon,
    roles: ['DISPATCHER'],
    description: 'Призначення екіпажу на рейси'
  },
  {
    id: 'crew-view',
    name: 'Екіпаж',
    path: '/crew',
    icon: UsersIcon,
    roles: ['DISPATCHER'],
    description: 'Перегляд інформації про екіпаж'
  },
  {
    id: 'schedule',
    name: 'Розклад',
    path: '/schedule',
    icon: CalendarDaysIcon,
    roles: ['DISPATCHER'],
    description: 'Розклад рейсів та екіпажу'
  }
]

// Об'єднання всіх пунктів меню
const allMenuItems = [
  ...baseMenuItems,
  ...adminMenuItems,
  ...dispatcherMenuItems
]

/**
 * Отримати пункти меню для конкретної ролі користувача
 * @param {string} userRole - Роль користувача ('ADMIN', 'DISPATCHER')
 * @returns {Array} Масив пунктів меню доступних для цієї ролі
 */
export const getMenuItemsForRole = (userRole) => {
  if (!userRole) return []

  return allMenuItems.filter(item =>
    item.roles.includes(userRole.toUpperCase())
  ).map(item => ({
    ...item,
    // Фільтруємо підпункти також за роллю, якщо вони є
    subItems: item.subItems ? item.subItems.filter(subItem =>
      !subItem.roles || subItem.roles.includes(userRole.toUpperCase())
    ) : undefined
  }))
}

/**
 * Отримати всі пункти меню (для адміністрування)
 * @returns {Array} Всі доступні пункти меню
 */
export const getAllMenuItems = () => allMenuItems

/**
 * Знайти пункт меню за ID
 * @param {string} itemId - ID пункту меню
 * @returns {Object|null} Пункт меню або null якщо не знайдено
 */
export const getMenuItemById = (itemId) => {
  for (const item of allMenuItems) {
    if (item.id === itemId) return item

    if (item.subItems) {
      const subItem = item.subItems.find(sub => sub.id === itemId)
      if (subItem) return { ...subItem, parent: item }
    }
  }
  return null
}

/**
 * Перевірити чи має користувач доступ до конкретного пункту меню
 * @param {string} itemId - ID пункту меню
 * @param {string} userRole - Роль користувача
 * @returns {boolean} true якщо користувач має доступ
 */
export const hasAccessToMenuItem = (itemId, userRole) => {
  const item = getMenuItemById(itemId)
  if (!item) return false

  const roles = item.roles || (item.parent && item.parent.roles) || []
  return roles.includes(userRole?.toUpperCase())
}

/**
 * Отримати хлібні крихти для поточного маршруту
 * @param {string} currentPath - Поточний шлях
 * @param {string} userRole - Роль користувача
 * @returns {Array} Масив хлібних крихт
 */
export const getBreadcrumbs = (currentPath, userRole) => {
  const breadcrumbs = [
    { name: 'Головна', path: '/dashboard' }
  ]

  const menuItems = getMenuItemsForRole(userRole)

  for (const item of menuItems) {
    if (item.path === currentPath) {
      if (item.id !== 'dashboard') {
        breadcrumbs.push({ name: item.name, path: item.path })
      }
      break
    }

    if (item.subItems) {
      const subItem = item.subItems.find(sub => sub.path === currentPath)
      if (subItem) {
        breadcrumbs.push({ name: item.name, path: item.path })
        breadcrumbs.push({ name: subItem.name, path: subItem.path })
        break
      }
    }
  }

  return breadcrumbs
}

/**
 * Конфігурація для мобільного меню
 */
export const mobileMenuConfig = {
  // Пункти які завжди видимі в мобільному меню
  alwaysVisible: ['dashboard'],
  // Максимальна кількість пунктів в мобільному меню
  maxItems: 5,
  // Чи показувати підпункти в мобільному меню
  showSubItems: false
}

/**
 * Конфігурація швидких дій (для floating action button або швидкого доступу)
 */
export const quickActionsConfig = {
  ADMIN: [
    {
      id: 'create-flight',
      name: 'Створити рейс',
      action: 'navigate',
      target: '/flights/create',
      icon: AirplaneIcon,
      color: 'blue'
    },
    {
      id: 'add-crew',
      name: 'Додати екіпаж',
      action: 'navigate',
      target: '/crew/create',
      icon: UsersIcon,
      color: 'green'
    }
  ],
  DISPATCHER: [
    {
      id: 'assign-crew',
      name: 'Призначити екіпаж',
      action: 'navigate',
      target: '/assignments/create',
      icon: ClipboardDocumentListIcon,
      color: 'purple'
    },
    {
      id: 'view-schedule',
      name: 'Переглянути розклад',
      action: 'navigate',
      target: '/schedule',
      icon: CalendarDaysIcon,
      color: 'orange'
    }
  ]
}

/**
 * Отримати швидкі дії для ролі користувача
 * @param {string} userRole - Роль користувача
 * @returns {Array} Масив швидких дій
 */
export const getQuickActionsForRole = (userRole) => {
  return quickActionsConfig[userRole?.toUpperCase()] || []
}

// За замовчуванням експортуємо функцію для отримання меню
export default getMenuItemsForRole
