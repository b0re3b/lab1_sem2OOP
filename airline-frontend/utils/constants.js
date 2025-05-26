/**
 * Константи та енуми для системи управління авіакомпанією
 */

// Ролі користувачів
export const USER_ROLES = {
  ADMIN: 'ADMIN',
  DISPATCHER: 'DISPATCHER'
};

export const USER_ROLE_LABELS = {
  [USER_ROLES.ADMIN]: 'Адміністратор',
  [USER_ROLES.DISPATCHER]: 'Диспетчер'
};

// Статуси рейсів
export const FLIGHT_STATUS = {
  SCHEDULED: 'SCHEDULED',
  DELAYED: 'DELAYED',
  CANCELLED: 'CANCELLED',
  COMPLETED: 'COMPLETED'
};

export const FLIGHT_STATUS_LABELS = {
  [FLIGHT_STATUS.SCHEDULED]: 'Заплановано',
  [FLIGHT_STATUS.DELAYED]: 'Затримано',
  [FLIGHT_STATUS.CANCELLED]: 'Скасовано',
  [FLIGHT_STATUS.COMPLETED]: 'Завершено'
};

// Статуси призначень
export const ASSIGNMENT_STATUS = {
  ASSIGNED: 'ASSIGNED',
  CONFIRMED: 'CONFIRMED',
  CANCELLED: 'CANCELLED'
};

export const ASSIGNMENT_STATUS_LABELS = {
  [ASSIGNMENT_STATUS.ASSIGNED]: 'Призначено',
  [ASSIGNMENT_STATUS.CONFIRMED]: 'Підтверджено',
  [ASSIGNMENT_STATUS.CANCELLED]: 'Скасовано'
};

// Рівні сертифікації
export const CERTIFICATION_LEVELS = {
  JUNIOR: 'JUNIOR',
  SENIOR: 'SENIOR',
  CAPTAIN: 'CAPTAIN'
};

export const CERTIFICATION_LEVEL_LABELS = {
  [CERTIFICATION_LEVELS.JUNIOR]: 'Молодший',
  [CERTIFICATION_LEVELS.SENIOR]: 'Старший',
  [CERTIFICATION_LEVELS.CAPTAIN]: 'Капітан'
};

// Посади екіпажу
export const CREW_POSITIONS = {
  PILOT: 'PILOT',
  CO_PILOT: 'CO_PILOT',
  NAVIGATOR: 'NAVIGATOR',
  RADIO_OPERATOR: 'RADIO_OPERATOR',
  FLIGHT_ATTENDANT: 'FLIGHT_ATTENDANT',
  FLIGHT_ENGINEER: 'FLIGHT_ENGINEER'
};

export const CREW_POSITION_LABELS = {
  [CREW_POSITIONS.PILOT]: 'Пілот',
  [CREW_POSITIONS.CO_PILOT]: 'Другий пілот',
  [CREW_POSITIONS.NAVIGATOR]: 'Штурман',
  [CREW_POSITIONS.RADIO_OPERATOR]: 'Радист',
  [CREW_POSITIONS.FLIGHT_ATTENDANT]: 'Бортпровідник',
  [CREW_POSITIONS.FLIGHT_ENGINEER]: 'Бортінженер'
};

// Статуси укомплектованості
export const STAFFING_STATUS = {
  FULLY_STAFFED: 'FULLY_STAFFED',
  PARTIALLY_STAFFED: 'PARTIALLY_STAFFED',
  NOT_STAFFED: 'NOT_STAFFED'
};

export const STAFFING_STATUS_LABELS = {
  [STAFFING_STATUS.FULLY_STAFFED]: 'Повністю укомплектовано',
  [STAFFING_STATUS.PARTIALLY_STAFFED]: 'Частково укомплектовано',
  [STAFFING_STATUS.NOT_STAFFED]: 'Не укомплектовано'
};

// Типи літаків
export const AIRCRAFT_TYPES = [
  'Boeing 737',
  'Boeing 747',
  'Boeing 777',
  'Boeing 787',
  'Airbus A320',
  'Airbus A330',
  'Airbus A340',
  'Airbus A350',
  'Airbus A380',
  'Embraer E190',
  'Bombardier CRJ'
];

// Міста України
export const UKRAINIAN_CITIES = [
  'Київ',
  'Харків',
  'Одеса',
  'Дніпро',
  'Донецьк',
  'Запоріжжя',
  'Львів',
  'Кривий Ріг',
  'Миколаїв',
  'Маріуполь',
  'Луганськ',
  'Вінниця',
  'Макіївка',
  'Севастополь',
  'Сімферополь',
  'Херсон',
  'Полтава',
  'Чернігів',
  'Черкаси',
  'Суми',
  'Житомир',
  'Хмельницький',
  'Чернівці',
  'Рівне',
  'Камʼянське',
  'Кропивницький',
  'Івано-Франківськ',
  'Тернопіль',
  'Луцьк',
  'Ужгород'
];

// Кольори для статусів
export const STATUS_COLORS = {
  // Статуси рейсів
  [FLIGHT_STATUS.SCHEDULED]: 'blue',
  [FLIGHT_STATUS.DELAYED]: 'yellow',
  [FLIGHT_STATUS.CANCELLED]: 'red',
  [FLIGHT_STATUS.COMPLETED]: 'green',

  // Статуси призначень
  [ASSIGNMENT_STATUS.ASSIGNED]: 'blue',
  [ASSIGNMENT_STATUS.CONFIRMED]: 'green',
  [ASSIGNMENT_STATUS.CANCELLED]: 'red',

  // Рівні сертифікації
  [CERTIFICATION_LEVELS.JUNIOR]: 'gray',
  [CERTIFICATION_LEVELS.SENIOR]: 'blue',
  [CERTIFICATION_LEVELS.CAPTAIN]: 'purple',

  // Статуси укомплектованості
  [STAFFING_STATUS.FULLY_STAFFED]: 'green',
  [STAFFING_STATUS.PARTIALLY_STAFFED]: 'yellow',
  [STAFFING_STATUS.NOT_STAFFED]: 'red'
};

// Налаштування пагінації
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [5, 10, 20, 50],
  MAX_VISIBLE_PAGES: 5
};

// Налаштування валідації
export const VALIDATION = {
  FLIGHT_NUMBER: {
    MIN_LENGTH: 4,
    MAX_LENGTH: 10,
    PATTERN: /^[A-Z]{2}\d{3,4}$/
  },
  EMPLOYEE_ID: {
    MIN_LENGTH: 3,
    MAX_LENGTH: 20,
    PATTERN: /^[A-Z0-9]+$/
  },
  PHONE: {
    PATTERN: /^\+380\d{9}$/
  },
  EMAIL: {
    PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  },
  NAME: {
    MIN_LENGTH: 2,
    MAX_LENGTH: 100,
    PATTERN: /^[а-яіїєґА-ЯІЇЄҐ\s\-']+$/u
  }
};

// Повідомлення
export const MESSAGES = {
  SUCCESS: {
    CREATED: 'Запис успішно створено',
    UPDATED: 'Запис успішно оновлено',
    DELETED: 'Запис успішно видалено',
    ASSIGNED: 'Екіпаж успішно призначено',
    CONFIRMED: 'Призначення підтверджено',
    CANCELLED: 'Призначення скасовано'
  },
  ERROR: {
    GENERIC: 'Виникла помилка. Спробуйте ще раз',
    NETWORK: 'Помилка з\'єднання з сервером',
    UNAUTHORIZED: 'Недостатньо прав доступу',
    NOT_FOUND: 'Запис не знайдено',
    VALIDATION: 'Помилка валідації даних',
    CONFLICT: 'Конфлікт даних. Можливо запис вже існує'
  },
  CONFIRM: {
    DELETE: 'Ви впевнені, що хочете видалити цей запис?',
    CANCEL: 'Ви впевнені, що хочете скасувати це призначення?',
    LOGOUT: 'Ви впевнені, що хочете вийти з системи?'
  }
};

// Налаштування форм
export const FORM_CONFIG = {
  FLIGHT: {
    FIELDS: [
      { key: 'flight_number', label: 'Номер рейсу', type: 'text', required: true },
      { key: 'departure_city', label: 'Місто відправлення', type: 'select', required: true, options: UKRAINIAN_CITIES },
      { key: 'arrival_city', label: 'Місто прибуття', type: 'select', required: true, options: UKRAINIAN_CITIES },
      { key: 'departure_time', label: 'Час відправлення', type: 'datetime-local', required: true },
      { key: 'arrival_time', label: 'Час прибуття', type: 'datetime-local', required: true },
      { key: 'aircraft_type', label: 'Тип літака', type: 'select', required: true, options: AIRCRAFT_TYPES },
      { key: 'crew_required', label: 'Потрібно екіпажу', type: 'number', required: true, min: 1, max: 20 },
      { key: 'status', label: 'Статус', type: 'select', required: true, options: Object.values(FLIGHT_STATUS) }
    ]
  },
  CREW_MEMBER: {
    FIELDS: [
      { key: 'employee_id', label: 'Табельний номер', type: 'text', required: true },
      { key: 'first_name', label: "Ім'я", type: 'text', required: true },
      { key: 'last_name', label: 'Прізвище', type: 'text', required: true },
      { key: 'position_id', label: 'Посада', type: 'select', required: true },
      { key: 'experience_years', label: 'Досвід (років)', type: 'number', required: true, min: 0, max: 50 },
      { key: 'certification_level', label: 'Рівень сертифікації', type: 'select', required: true, options: Object.values(CERTIFICATION_LEVELS) },
      { key: 'phone', label: 'Телефон', type: 'tel', required: false },
      { key: 'email', label: 'Email', type: 'email', required: false },
      { key: 'is_available', label: 'Доступний', type: 'checkbox', required: false }
    ]
  }
};

// Конфігурація таблиць
export const TABLE_CONFIG = {
  FLIGHTS: {
    COLUMNS: [
      { key: 'flight_number', label: 'Рейс', sortable: true },
      { key: 'departure_city', label: 'Відправлення', sortable: true },
      { key: 'arrival_city', label: 'Прибуття', sortable: true },
      { key: 'departure_time', label: 'Час відправлення', sortable: true, type: 'datetime' },
      { key: 'arrival_time', label: 'Час прибуття', sortable: true, type: 'datetime' },
      { key: 'aircraft_type', label: 'Літак', sortable: true },
      { key: 'status', label: 'Статус', sortable: true, type: 'status' },
      { key: 'assigned_crew_count', label: 'Екіпаж', sortable: true },
      { key: 'actions', label: 'Дії', sortable: false }
    ],
    SEARCH_FIELDS: ['flight_number', 'departure_city', 'arrival_city', 'aircraft_type']
  },
  CREW: {
    COLUMNS: [
      { key: 'employee_id', label: 'Табельний №', sortable: true },
      { key: 'full_name', label: "Ім'я", sortable: true },
      { key: 'position_name', label: 'Посада', sortable: true },
      { key: 'experience_years', label: 'Досвід', sortable: true },
      { key: 'certification_level', label: 'Рівень', sortable: true, type: 'status' },
      { key: 'is_available', label: 'Доступний', sortable: true, type: 'boolean' },
      { key: 'phone', label: 'Телефон', sortable: false },
      { key: 'actions', label: 'Дії', sortable: false }
    ],
    SEARCH_FIELDS: ['employee_id', 'first_name', 'last_name', 'position_name']
  },
  ASSIGNMENTS: {
    COLUMNS: [
      { key: 'flight_number', label: 'Рейс', sortable: true },
      { key: 'crew_member_name', label: 'Член екіпажу', sortable: true },
      { key: 'position_name', label: 'Посада', sortable: true },
      { key: 'departure_time', label: 'Час відправлення', sortable: true, type: 'datetime' },
      { key: 'status', label: 'Статус', sortable: true, type: 'status' },
      { key: 'assigned_at', label: 'Призначено', sortable: true, type: 'datetime' },
      { key: 'actions', label: 'Дії', sortable: false }
    ],
    SEARCH_FIELDS: ['flight_number', 'crew_member_name', 'position_name']
  }
};

// API endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
    KEYCLOAK_LOGIN: '/auth/keycloak/login',
    KEYCLOAK_CALLBACK: '/auth/keycloak/callback'
  },
  FLIGHTS: {
    BASE: '/flights',
    BY_ID: (id) => `/flights/${id}`,
    BY_NUMBER: (number) => `/flights/number/${number}`,
    SCHEDULE: '/flights/schedule',
    NEEDING_CREW: '/flights/needing-crew'
  },
  CREW: {
    BASE: '/crew',
    BY_ID: (id) => `/crew/${id}`,
    BY_EMPLOYEE_ID: (employeeId) => `/crew/employee/${employeeId}`,
    AVAILABLE: '/crew/available',
    POSITIONS: '/crew/positions',
    RECOMMENDATIONS: '/crew/recommendations'
  },
  ASSIGNMENTS: {
    BASE: '/assignments',
    BY_ID: (id) => `/assignments/${id}`,
    BY_FLIGHT: (flightId) => `/assignments/flight/${flightId}`,
    BY_CREW: (crewId) => `/assignments/crew/${crewId}`,
    AUTO_ASSIGN: '/assignments/auto-assign',
    SUMMARY: '/assignments/summary',
    STATISTICS: '/assignments/statistics'
  }
};

// Налаштування для локального зберігання
export const STORAGE_KEYS = {
  TOKEN: 'airline_token',
  REFRESH_TOKEN: 'airline_refresh_token',
  USER: 'airline_user',
  THEME: 'airline_theme',
  LANGUAGE: 'airline_language',
  TABLE_SETTINGS: 'airline_table_settings'
};

// Експорт всіх констант як default об'єкт
export default {
  USER_ROLES,
  USER_ROLE_LABELS,
  FLIGHT_STATUS,
  FLIGHT_STATUS_LABELS,
  ASSIGNMENT_STATUS,
  ASSIGNMENT_STATUS_LABELS,
  CERTIFICATION_LEVELS,
  CERTIFICATION_LEVEL_LABELS,
  CREW_POSITIONS,
  CREW_POSITION_LABELS,
  STAFFING_STATUS,
  STAFFING_STATUS_LABELS,
  AIRCRAFT_TYPES,
  UKRAINIAN_CITIES,
  STATUS_COLORS,
  PAGINATION,
  VALIDATION,
  MESSAGES,
  FORM_CONFIG,
  TABLE_CONFIG,
  API_ENDPOINTS,
  STORAGE_KEYS
};
