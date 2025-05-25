import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class UserRole(Enum):
    """Ролі користувачів у системі"""
    ADMIN = "ADMIN"
    DISPATCHER = "DISPATCHER"


class FlightStatus(Enum):
    """Статуси рейсів"""
    SCHEDULED = "SCHEDULED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class CertificationLevel(Enum):
    """Рівні сертифікації екіпажу"""
    JUNIOR = "JUNIOR"
    SENIOR = "SENIOR"
    CAPTAIN = "CAPTAIN"


class AssignmentStatus(Enum):
    """Статуси призначень"""
    ASSIGNED = "ASSIGNED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class ValidationError(Exception):
    """Кастомний клас для помилок валідації"""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class BaseValidator:
    """Базовий клас для валідаторів"""

    @staticmethod
    def validate_required_field(value: Any, field_name: str) -> None:
        """Перевірка обов'язкового поля"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(field_name, "Поле є обов'язковим")

    @staticmethod
    def validate_string_length(value: str, field_name: str, min_length: int = 0, max_length: int = None) -> None:
        """Перевірка довжини рядка"""
        if value is None:
            return

        length = len(value.strip())
        if length < min_length:
            raise ValidationError(field_name, f"Мінімальна довжина: {min_length} символів")

        if max_length and length > max_length:
            raise ValidationError(field_name, f"Максимальна довжина: {max_length} символів")

    @staticmethod
    def validate_enum_value(value: str, enum_class: Enum, field_name: str) -> None:
        """Перевірка значення з enum"""
        if value not in [e.value for e in enum_class]:
            valid_values = [e.value for e in enum_class]
            raise ValidationError(field_name, f"Допустимі значення: {', '.join(valid_values)}")


class UserValidator(BaseValidator):
    """Валідатор для користувачів системи"""

    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,50}$')

    @classmethod
    def validate_user_data(cls, user_data: Dict[str, Any]) -> List[str]:
        """Валідація даних користувача"""
        errors = []

        try:
            # Перевірка Keycloak ID
            cls.validate_required_field(user_data.get('keycloak_id'), 'keycloak_id')
            cls.validate_keycloak_id(user_data.get('keycloak_id'))
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка username
            cls.validate_required_field(user_data.get('username'), 'username')
            cls.validate_username(user_data.get('username'))
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка email
            cls.validate_required_field(user_data.get('email'), 'email')
            cls.validate_email(user_data.get('email'))
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка імені та прізвища
            cls.validate_required_field(user_data.get('first_name'), 'first_name')
            cls.validate_string_length(user_data.get('first_name'), 'first_name', 2, 100)

            cls.validate_required_field(user_data.get('last_name'), 'last_name')
            cls.validate_string_length(user_data.get('last_name'), 'last_name', 2, 100)
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка ролі
            cls.validate_required_field(user_data.get('role'), 'role')
            cls.validate_enum_value(user_data.get('role'), UserRole, 'role')
        except ValidationError as e:
            errors.append(str(e))

        return errors

    @classmethod
    def validate_keycloak_id(cls, keycloak_id: str) -> None:
        """Валідація Keycloak ID"""
        if not keycloak_id or len(keycloak_id.strip()) < 10:
            raise ValidationError('keycloak_id', 'Некоректний Keycloak ID')

    @classmethod
    def validate_username(cls, username: str) -> None:
        """Валідація username"""
        if not username or not cls.USERNAME_PATTERN.match(username):
            raise ValidationError('username',
                                  'Username повинен містити лише літери, цифри та підкреслення (3-50 символів)')

    @classmethod
    def validate_email(cls, email: str) -> None:
        """Валідація email"""
        if not email or not cls.EMAIL_PATTERN.match(email):
            raise ValidationError('email', 'Некоректний формат email')


class FlightValidator(BaseValidator):
    """Валідатор для рейсів"""

    FLIGHT_NUMBER_PATTERN = re.compile(r'^[A-Z]{2}\d{3,4}$')
    AIRCRAFT_TYPES = ['Boeing 737', 'Boeing 747', 'Airbus A320', 'Airbus A330', 'Embraer 190']

    @classmethod
    def validate_flight_data(cls, flight_data: Dict[str, Any]) -> List[str]:
        """Валідація даних рейсу"""
        errors = []

        try:
            # Перевірка номера рейсу
            cls.validate_required_field(flight_data.get('flight_number'), 'flight_number')
            cls.validate_flight_number(flight_data.get('flight_number'))
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка міст
            cls.validate_required_field(flight_data.get('departure_city'), 'departure_city')
            cls.validate_string_length(flight_data.get('departure_city'), 'departure_city', 2, 100)

            cls.validate_required_field(flight_data.get('arrival_city'), 'arrival_city')
            cls.validate_string_length(flight_data.get('arrival_city'), 'arrival_city', 2, 100)

            # Перевірка, що міста відрізняються
            if (flight_data.get('departure_city') and flight_data.get('arrival_city') and
                    flight_data.get('departure_city').strip().lower() == flight_data.get(
                        'arrival_city').strip().lower()):
                raise ValidationError('cities', 'Місто відправлення та прибуття не можуть бути однаковими')
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка часу
            cls.validate_flight_times(
                flight_data.get('departure_time'),
                flight_data.get('arrival_time')
            )
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка типу літака
            cls.validate_required_field(flight_data.get('aircraft_type'), 'aircraft_type')
            cls.validate_aircraft_type(flight_data.get('aircraft_type'))
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка статусу
            if flight_data.get('status'):
                cls.validate_enum_value(flight_data.get('status'), FlightStatus, 'status')
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка кількості екіпажу
            crew_required = flight_data.get('crew_required', 4)
            cls.validate_crew_required(crew_required)
        except ValidationError as e:
            errors.append(str(e))

        return errors

    @classmethod
    def validate_flight_number(cls, flight_number: str) -> None:
        """Валідація номера рейсу"""
        if not flight_number or not cls.FLIGHT_NUMBER_PATTERN.match(flight_number):
            raise ValidationError('flight_number', 'Номер рейсу повинен мати формат: XX123 або XX1234 (літери + цифри)')

    @classmethod
    def validate_aircraft_type(cls, aircraft_type: str) -> None:
        """Валідація типу літака"""
        if aircraft_type not in cls.AIRCRAFT_TYPES:
            raise ValidationError('aircraft_type', f'Допустимі типи літаків: {", ".join(cls.AIRCRAFT_TYPES)}')

    @classmethod
    def validate_flight_times(cls, departure_time: Any, arrival_time: Any) -> None:
        """Валідація часу рейсу"""
        cls.validate_required_field(departure_time, 'departure_time')
        cls.validate_required_field(arrival_time, 'arrival_time')

        # Конвертація в datetime якщо потрібно
        if isinstance(departure_time, str):
            try:
                departure_time = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError('departure_time', 'Некоректний формат дати/часу')

        if isinstance(arrival_time, str):
            try:
                arrival_time = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError('arrival_time', 'Некоректний формат дати/часу')

        # Перевірка логічності часу
        if departure_time >= arrival_time:
            raise ValidationError('flight_times', 'Час прибуття повинен бути пізніше часу відправлення')

        # Перевірка мінімальної тривалості рейсу (30 хвилин)
        if (arrival_time - departure_time) < timedelta(minutes=30):
            raise ValidationError('flight_times', 'Мінімальна тривалість рейсу: 30 хвилин')

        # Перевірка максимальної тривалості рейсу (24 години)
        if (arrival_time - departure_time) > timedelta(hours=24):
            raise ValidationError('flight_times', 'Максимальна тривалість рейсу: 24 години')

        # Перевірка, що рейс не в минулому
        if departure_time < datetime.now():
            raise ValidationError('departure_time', 'Час відправлення не може бути в минулому')

    @classmethod
    def validate_crew_required(cls, crew_required: int) -> None:
        """Валідація кількості необхідного екіпажу"""
        if not isinstance(crew_required, int) or crew_required < 2 or crew_required > 12:
            raise ValidationError('crew_required', 'Кількість екіпажу повинна бути від 2 до 12 осіб')


class CrewValidator(BaseValidator):
    """Валідатор для членів екіпажу"""

    EMPLOYEE_ID_PATTERN = re.compile(r'^[A-Z]{1,3}\d{3,4}$')
    PHONE_PATTERN = re.compile(r'^\+380\d{9}$')

    @classmethod
    def validate_crew_member_data(cls, crew_data: Dict[str, Any]) -> List[str]:
        """Валідація даних члена екіпажу"""
        errors = []

        try:
            # Перевірка employee_id
            cls.validate_required_field(crew_data.get('employee_id'), 'employee_id')
            cls.validate_employee_id(crew_data.get('employee_id'))
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка імені та прізвища
            cls.validate_required_field(crew_data.get('first_name'), 'first_name')
            cls.validate_string_length(crew_data.get('first_name'), 'first_name', 2, 100)

            cls.validate_required_field(crew_data.get('last_name'), 'last_name')
            cls.validate_string_length(crew_data.get('last_name'), 'last_name', 2, 100)
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка посади
            cls.validate_required_field(crew_data.get('position_id'), 'position_id')
            if not isinstance(crew_data.get('position_id'), int) or crew_data.get('position_id') <= 0:
                raise ValidationError('position_id', 'Некоректний ID посади')
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка досвіду
            experience = crew_data.get('experience_years', 0)
            cls.validate_experience_years(experience)
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка рівня сертифікації
            if crew_data.get('certification_level'):
                cls.validate_enum_value(crew_data.get('certification_level'), CertificationLevel, 'certification_level')
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка телефону
            if crew_data.get('phone'):
                cls.validate_phone(crew_data.get('phone'))
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка email
            if crew_data.get('email'):
                UserValidator.validate_email(crew_data.get('email'))
        except ValidationError as e:
            errors.append(str(e))

        return errors

    @classmethod
    def validate_employee_id(cls, employee_id: str) -> None:
        """Валідація ID співробітника"""
        if not employee_id or not cls.EMPLOYEE_ID_PATTERN.match(employee_id):
            raise ValidationError('employee_id', 'ID співробітника повинен мати формат: P001, FA123, тощо')

    @classmethod
    def validate_experience_years(cls, experience_years: int) -> None:
        """Валідація років досвіду"""
        if not isinstance(experience_years, int) or experience_years < 0 or experience_years > 50:
            raise ValidationError('experience_years', 'Роки досвіду повинні бути від 0 до 50')

    @classmethod
    def validate_phone(cls, phone: str) -> None:
        """Валідація телефону"""
        if not cls.PHONE_PATTERN.match(phone):
            raise ValidationError('phone', 'Телефон повинен мати формат: +380XXXXXXXXX')


class AssignmentValidator(BaseValidator):
    """Валідатор для призначень екіпажу"""

    @classmethod
    def validate_assignment_data(cls, assignment_data: Dict[str, Any]) -> List[str]:
        """Валідація даних призначення"""
        errors = []

        try:
            # Перевірка ID рейсу
            cls.validate_required_field(assignment_data.get('flight_id'), 'flight_id')
            if not isinstance(assignment_data.get('flight_id'), int) or assignment_data.get('flight_id') <= 0:
                raise ValidationError('flight_id', 'Некоректний ID рейсу')
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка ID члена екіпажу
            cls.validate_required_field(assignment_data.get('crew_member_id'), 'crew_member_id')
            if not isinstance(assignment_data.get('crew_member_id'), int) or assignment_data.get('crew_member_id') <= 0:
                raise ValidationError('crew_member_id', 'Некоректний ID члена екіпажу')
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка ID користувача, який призначає
            cls.validate_required_field(assignment_data.get('assigned_by'), 'assigned_by')
            if not isinstance(assignment_data.get('assigned_by'), int) or assignment_data.get('assigned_by') <= 0:
                raise ValidationError('assigned_by', 'Некоректний ID користувача')
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка статусу
            if assignment_data.get('status'):
                cls.validate_enum_value(assignment_data.get('status'), AssignmentStatus, 'status')
        except ValidationError as e:
            errors.append(str(e))

        try:
            # Перевірка приміток
            if assignment_data.get('notes'):
                cls.validate_string_length(assignment_data.get('notes'), 'notes', 0, 1000)
        except ValidationError as e:
            errors.append(str(e))

        return errors


class GeneralValidator:
    """Загальні валідатори"""

    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime, field_name: str = 'date_range') -> None:
        """Валідація діапазону дат"""
        if start_date >= end_date:
            raise ValidationError(field_name, 'Дата початку повинна бути раніше дати закінчення')

    @staticmethod
    def validate_positive_integer(value: Any, field_name: str) -> None:
        """Валідація додатного цілого числа"""
        if not isinstance(value, int) or value <= 0:
            raise ValidationError(field_name, 'Значення повинно бути додатним цілим числом')

    @staticmethod
    def validate_uuid(value: str, field_name: str) -> None:
        """Валідація UUID"""
        try:
            uuid.UUID(value)
        except (ValueError, TypeError):
            raise ValidationError(field_name, 'Некоректний формат UUID')

    @staticmethod
    def sanitize_string(value: str) -> str:
        """Очищення рядка від небезпечних символів"""
        if not value:
            return ""

        # Видаляємо небезпечні символи для SQL ін'єкцій
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        sanitized = value

        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')

        return sanitized.strip()