/**
 * Загальні допоміжні функції для фронтенду
 */

// Форматування дати та часу
export const formatDateTime = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('uk-UA', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('uk-UA');
};

export const formatTime = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleTimeString('uk-UA', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Обчислення тривалості польоту
export const calculateFlightDuration = (departure, arrival) => {
  if (!departure || !arrival) return '';
  const diff = new Date(arrival) - new Date(departure);
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  return `${hours}г ${minutes}хв`;
};

// Перевірка чи дата в майбутньому
export const isFutureDate = (dateString) => {
  if (!dateString) return false;
  return new Date(dateString) > new Date();
};

// Перевірка чи дата сьогодні
export const isToday = (dateString) => {
  if (!dateString) return false;
  const today = new Date();
  const date = new Date(dateString);
  return date.toDateString() === today.toDateString();
};

// Валідація email
export const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

// Валідація телефону (українські номери)
export const validatePhone = (phone) => {
  const re = /^\+380\d{9}$/;
  return re.test(phone);
};

// Генерація кольору для статусу
export const getStatusColor = (status) => {
  const colorMap = {
    // Статуси рейсів
    'SCHEDULED': 'text-blue-600 bg-blue-100',
    'DELAYED': 'text-yellow-600 bg-yellow-100',
    'CANCELLED': 'text-red-600 bg-red-100',
    'COMPLETED': 'text-green-600 bg-green-100',

    // Статуси призначень
    'ASSIGNED': 'text-blue-600 bg-blue-100',
    'CONFIRMED': 'text-green-600 bg-green-100',

    // Рівні сертифікації
    'JUNIOR': 'text-gray-600 bg-gray-100',
    'SENIOR': 'text-blue-600 bg-blue-100',
    'CAPTAIN': 'text-purple-600 bg-purple-100',

    // Статуси укомплектованості
    'FULLY_STAFFED': 'text-green-600 bg-green-100',
    'PARTIALLY_STAFFED': 'text-yellow-600 bg-yellow-100',
    'NOT_STAFFED': 'text-red-600 bg-red-100'
  };

  return colorMap[status] || 'text-gray-600 bg-gray-100';
};

// Переклад статусів
export const translateStatus = (status) => {
  const translations = {
    // Статуси рейсів
    'SCHEDULED': 'Заплановано',
    'DELAYED': 'Затримано',
    'CANCELLED': 'Скасовано',
    'COMPLETED': 'Завершено',

    // Статуси призначень
    'ASSIGNED': 'Призначено',
    'CONFIRMED': 'Підтверджено',

    // Рівні сертифікації
    'JUNIOR': 'Молодший',
    'SENIOR': 'Старший',
    'CAPTAIN': "Капітан",

    // Статуси укомплектованості
    'FULLY_STAFFED': 'Повністю укомплектовано',
    'PARTIALLY_STAFFED': 'Частково укомплектовано',
    'NOT_STAFFED': 'Не укомплектовано',

    // Ролі користувачів
    'ADMIN': 'Адміністратор',
    'DISPATCHER': 'Диспетчер'
  };

  return translations[status] || status;
};

// Переклад посад
export const translatePosition = (position) => {
  const translations = {
    'PILOT': 'Пілот',
    'CO_PILOT': 'Другий пілот',
    'NAVIGATOR': 'Штурман',
    'RADIO_OPERATOR': 'Радист',
    'FLIGHT_ATTENDANT': 'Бортпровідник',
    'FLIGHT_ENGINEER': 'Бортінженер'
  };

  return translations[position] || position;
};

// Сортування масиву об'єктів
export const sortBy = (array, key, direction = 'asc') => {
  return [...array].sort((a, b) => {
    const aVal = getNestedValue(a, key);
    const bVal = getNestedValue(b, key);

    if (aVal < bVal) return direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return direction === 'asc' ? 1 : -1;
    return 0;
  });
};

// Отримання вкладеного значення з об'єкта
export const getNestedValue = (obj, path) => {
  return path.split('.').reduce((current, key) => current?.[key], obj);
};

// Фільтрація масиву
export const filterBy = (array, searchTerm, searchFields) => {
  if (!searchTerm) return array;

  const term = searchTerm.toLowerCase();
  return array.filter(item =>
    searchFields.some(field => {
      const value = getNestedValue(item, field);
      return value && value.toString().toLowerCase().includes(term);
    })
  );
};

// Дебаунсінг функції
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Генерація унікального ID
export const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

// Перевірка чи об'єкт порожній
export const isEmpty = (obj) => {
  return obj === null || obj === undefined ||
    (typeof obj === 'object' && Object.keys(obj).length === 0) ||
    (typeof obj === 'string' && obj.trim() === '');
};

// Глибоке клонування об'єкта
export const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime());
  if (obj instanceof Array) return obj.map(item => deepClone(item));

  const cloned = {};
  for (let key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloned[key] = deepClone(obj[key]);
    }
  }
  return cloned;
};

// Капіталізація першої літери
export const capitalize = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

// Скорочення тексту
export const truncate = (text, length = 50) => {
  if (!text) return '';
  return text.length > length ? text.substring(0, length) + '...' : text;
};

// Перевірка прав доступу
export const hasPermission = (userRole, requiredRole) => {
  const roleHierarchy = {
    'ADMIN': 2,
    'DISPATCHER': 1
  };

  return roleHierarchy[userRole] >= roleHierarchy[requiredRole];
};

// Форматування помилок
export const formatError = (error) => {
  if (typeof error === 'string') return error;

  if (error.response?.data?.detail) {
    return Array.isArray(error.response.data.detail)
      ? error.response.data.detail.map(e => e.msg).join(', ')
      : error.response.data.detail;
  }

  if (error.response?.data?.message) {
    return error.response.data.message;
  }

  if (error.message) {
    return error.message;
  }

  return 'Виникла невідома помилка';
};

// Експорт всіх функцій як default об'єкт
export default {
  formatDateTime,
  formatDate,
  formatTime,
  calculateFlightDuration,
  isFutureDate,
  isToday,
  validateEmail,
  validatePhone,
  getStatusColor,
  translateStatus,
  translatePosition,
  sortBy,
  getNestedValue,
  filterBy,
  debounce,
  generateId,
  isEmpty,
  deepClone,
  capitalize,
  truncate,
  hasPermission,
  formatError
};
