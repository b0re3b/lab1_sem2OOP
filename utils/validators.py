import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


@dataclass
class ValidationError:
    """Клас для представлення помилки валідації"""
    field: str
    message: str
    value: Any = None


class ValidationResult:
    """Результат валідації"""

    def __init__(self):
        self.is_valid = True
        self.errors: List[ValidationError] = []

    def add_error(self, field: str, message: str, value: Any = None):
        """Додати помилку валідації"""
        self.is_valid = False
        self.errors.append(ValidationError(field, message, value))

    def get_errors_dict(self) -> Dict[str, List[str]]:
        """Отримати помилки у вигляді словника"""
        errors_dict = {}
        for error in self.errors:
            if error.field not in errors_dict:
                errors_dict[error.field] = []
            errors_dict[error.field].append(error.message)
        return errors_dict

    def get_error_messages(self) -> List[str]:
        """Отримати всі повідомлення про помилки"""
        return [error.message for error in self.errors]


class BaseValidator(ABC):
    """Базовий клас для валідаторів"""

    @abstractmethod
    def validate(self, value: Any) -> ValidationResult:
        """Валідувати значення"""
        pass


class EmailValidator(BaseValidator):
    """Валідатор для email адрес"""

    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    def validate(self, email: str) -> ValidationResult:
        """Валідувати email адресу"""
        result = ValidationResult()

        if not email:
            result.add_error('email', 'Email не може бути пустим', email)
            return result

        if not isinstance(email, str):
            result.add_error('email', 'Email повинен бути рядком', email)
            return result

        if len(email) > 255:
            result.add_error('email', 'Email не може бути довшим за 255 символів', email)

        if not self.EMAIL_REGEX.match(email):
            result.add_error('email', 'Некоректний формат email адреси', email)

        return result

    def is_valid_email(self, email: str) -> bool:
        """Перевірити чи валідний email"""
        return self.validate(email).is_valid


class PhoneValidator(BaseValidator):
    """Валідатор для номерів телефонів"""

    PHONE_REGEX = re.compile(r'^\+380\d{9}$')

    def validate(self, phone: Optional[str]) -> ValidationResult:
        """Валідувати номер телефону"""
        result = ValidationResult()

        if phone is None:
            return result  # Phone є опціональним

        if not isinstance(phone, str):
            result.add_error('phone', 'Номер телефону повинен бути рядком', phone)
            return result

        if len(phone.strip()) == 0:
            return result  # Пустий телефон також валідний

        if not self.PHONE_REGEX.match(phone):
            result.add_error(
                'phone',
                'Номер телефону повинен бути у форматі +380XXXXXXXXX',
                phone
            )

        return result

    def is_valid_phone(self, phone: Optional[str]) -> bool:
        """Перевірити чи валідний номер телефону"""
        return self.validate(phone).is_valid


class DateTimeValidator(BaseValidator):
    """Валідатор для дат та часу"""

    def validate(self, dt: datetime, field_name: str = 'datetime') -> ValidationResult:
        """Валідувати datetime"""
        result = ValidationResult()

        if not dt:
            result.add_error(field_name, f'{field_name} не може бути пустим', dt)
            return result

        if not isinstance(dt, datetime):
            result.add_error(field_name, f'{field_name} повинен бути datetime об\'єктом', dt)
            return result

        # Перевірка що дата не в минулому (з допуском 5 хвилин)
        now = datetime.now()
        if dt < now - timedelta(minutes=5):
            result.add_error(
                field_name,
                f'{field_name} не може бути в минулому',
                dt
            )

        return result

    def validate_time_range(self, departure: datetime, arrival: datetime) -> ValidationResult:
        """Валідувати діапазон часу (відправлення -> прибуття)"""
        result = ValidationResult()

        # Валідуємо кожну дату окремо
        departure_result = self.validate(departure, 'departure_time')
        arrival_result = self.validate(arrival, 'arrival_time')

        # Додаємо помилки якщо є
        result.errors.extend(departure_result.errors)
        result.errors.extend(arrival_result.errors)

        if result.errors:
            result.is_valid = False
            return result

        # Перевіряємо що прибуття після відправлення
        if arrival <= departure:
            result.add_error(
                'arrival_time',
                'Час прибуття повинен бути після часу відправлення',
                {'departure': departure, 'arrival': arrival}
            )

        # Перевіряємо що рейс не довший за 24 години
        if arrival - departure > timedelta(hours=24):
            result.add_error(
                'arrival_time',
                'Тривалість рейсу не може перевищувати 24 години',
                {'departure': departure, 'arrival': arrival}
            )

        return result


class FlightValidator(BaseValidator):
    """Валідатор для рейсів"""

    VALID_STATUSES = {'SCHEDULED', 'DELAYED', 'CANCELLED', 'COMPLETED'}
    VALID_AIRCRAFT_TYPES = {
        'Boeing 737', 'Boeing 747', 'Boeing 777', 'Boeing 787',
        'Airbus A320', 'Airbus A330', 'Airbus A340', 'Airbus A350'
    }

    def __init__(self):
        self.datetime_validator = DateTimeValidator()

    def validate(self, flight_data: Dict[str, Any]) -> ValidationResult:
        """Валідувати дані рейсу"""
        result = ValidationResult()

        # Валідація номеру рейсу
        flight_number = flight_data.get('flight_number')
        if not flight_number:
            result.add_error('flight_number', 'Номер рейсу обов\'язковий', flight_number)
        elif not isinstance(flight_number, str):
            result.add_error('flight_number', 'Номер рейсу повинен бути рядком', flight_number)
        elif len(flight_number) > 10:
            result.add_error('flight_number', 'Номер рейсу не може бути довшим за 10 символів', flight_number)
        elif not re.match(r'^[A-Z]{2}\d{3,4}$', flight_number):
            result.add_error('flight_number', 'Номер рейсу повинен бути у форматі XX123 або XX1234', flight_number)

        # Валідація міст
        departure_city = flight_data.get('departure_city')
        arrival_city = flight_data.get('arrival_city')

        if not departure_city:
            result.add_error('departure_city', 'Місто відправлення обов\'язкове', departure_city)
        elif len(departure_city) > 100:
            result.add_error('departure_city', 'Назва міста не може бути довшою за 100 символів', departure_city)

        if not arrival_city:
            result.add_error('arrival_city', 'Місто прибуття обов\'язкове', arrival_city)
        elif len(arrival_city) > 100:
            result.add_error('arrival_city', 'Назва міста не може бути довшою за 100 символів', arrival_city)

        if departure_city and arrival_city and departure_city == arrival_city:
            result.add_error('arrival_city', 'Місто прибуття не може співпадати з містом відправлення', arrival_city)

        # Валідація часу
        departure_time = flight_data.get('departure_time')
        arrival_time = flight_data.get('arrival_time')

        if departure_time and arrival_time:
            time_result = self.datetime_validator.validate_time_range(departure_time, arrival_time)
            result.errors.extend(time_result.errors)

        # Валідація типу літака
        aircraft_type = flight_data.get('aircraft_type')
        if not aircraft_type:
            result.add_error('aircraft_type', 'Тип літака обов\'язковий', aircraft_type)
        elif aircraft_type not in self.VALID_AIRCRAFT_TYPES:
            result.add_error('aircraft_type',
                             f'Невалідний тип літака. Допустимі: {", ".join(self.VALID_AIRCRAFT_TYPES)}', aircraft_type)

        # Валідація статусу
        status = flight_data.get('status', 'SCHEDULED')
        if status not in self.VALID_STATUSES:
            result.add_error('status', f'Невалідний статус. Допустимі: {", ".join(self.VALID_STATUSES)}', status)

        # Валідація кількості екіпажу
        crew_required = flight_data.get('crew_required', 4)
        if not isinstance(crew_required, int) or crew_required < 2 or crew_required > 20:
            result.add_error('crew_required', 'Кількість екіпажу повинна бути від 2 до 20', crew_required)

        if result.errors:
            result.is_valid = False

        return result


class CrewValidator(BaseValidator):
    """Валідатор для членів екіпажу"""

    VALID_CERTIFICATION_LEVELS = {'JUNIOR', 'SENIOR', 'CAPTAIN'}
    VALID_POSITIONS = {'PILOT', 'CO_PILOT', 'FLIGHT_ATTENDANT', 'MECHANIC', 'DISPATCHER'}

    def __init__(self):
        self.email_validator = EmailValidator()
        self.phone_validator = PhoneValidator()

    def validate(self, crew_data: Dict[str, Any]) -> ValidationResult:
        """Валідувати дані члена екіпажу"""
        result = ValidationResult()

        # Валідація ID співробітника
        employee_id = crew_data.get('employee_id')
        if not employee_id:
            result.add_error('employee_id', 'ID співробітника обов\'язковий', employee_id)
        elif len(employee_id) > 20:
            result.add_error('employee_id', 'ID співробітника не може бути довшим за 20 символів', employee_id)
        elif not re.match(r'^[A-Z]+\d+$', employee_id):
            result.add_error('employee_id', 'ID співробітника повинен бути у форматі буква(и) + цифра(и)', employee_id)

        # Валідація імені та прізвища
        first_name = crew_data.get('first_name')
        last_name = crew_data.get('last_name')

        if not first_name:
            result.add_error('first_name', 'Ім\'я обов\'язкове', first_name)
        elif len(first_name) > 50:
            result.add_error('first_name', 'Ім\'я не може бути довшим за 50 символів', first_name)
        elif not re.match(r'^[a-zA-Zа-яА-ЯіІїЇєЄ\'\-\s]+$', first_name):
            result.add_error('first_name', 'Ім\'я може містити тільки букви, пробіли, апострофи та дефіси', first_name)

        if not last_name:
            result.add_error('last_name', 'Прізвище обов\'язкове', last_name)
        elif len(last_name) > 50:
            result.add_error('last_name', 'Прізвище не може бути довшим за 50 символів', last_name)
        elif not re.match(r'^[a-zA-Zа-яА-ЯіІїЇєЄ\'\-\s]+$', last_name):
            result.add_error('last_name', 'Прізвище може містити тільки букви, пробіли, апострофи та дефіси', last_name)

        # Валідація email
        email = crew_data.get('email')
        if email:
            email_result = self.email_validator.validate(email)
            result.errors.extend(email_result.errors)

        # Валідація телефону
        phone = crew_data.get('phone')
        phone_result = self.phone_validator.validate(phone)
        result.errors.extend(phone_result.errors)

        # Валідація позиції
        position = crew_data.get('position')
        if not position:
            result.add_error('position', 'Посада обов\'язкова', position)
        elif position not in self.VALID_POSITIONS:
            result.add_error('position', f'Невалідна посада. Допустимі: {", ".join(self.VALID_POSITIONS)}', position)

        # Валідація рівня сертифікації
        certification_level = crew_data.get('certification_level')
        if not certification_level:
            result.add_error('certification_level', 'Рівень сертифікації обов\'язковий', certification_level)
        elif certification_level not in self.VALID_CERTIFICATION_LEVELS:
            result.add_error('certification_level',
                             f'Невалідний рівень сертифікації. Допустимі: {", ".join(self.VALID_CERTIFICATION_LEVELS)}',
                             certification_level)

        # Валідація років досвіду
        years_experience = crew_data.get('years_experience', 0)
        if not isinstance(years_experience, int) or years_experience < 0 or years_experience > 50:
            result.add_error('years_experience', 'Років досвіду повинно бути від 0 до 50', years_experience)

        # Валідація дати народження
        birth_date = crew_data.get('birth_date')
        if birth_date:
            if not isinstance(birth_date, datetime):
                result.add_error('birth_date', 'Дата народження повинна бути datetime об\'єктом', birth_date)
            else:
                # Перевірка віку (від 18 до 70 років)
                today = datetime.now()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

                if age < 18:
                    result.add_error('birth_date', 'Вік повинен бути не менше 18 років', birth_date)
                elif age > 70:
                    result.add_error('birth_date', 'Вік не повинен перевищувати 70 років', birth_date)

        # Валідація зарплати
        salary = crew_data.get('salary')
        if salary is not None:
            if not isinstance(salary, (int, float)) or salary < 0:
                result.add_error('salary', 'Зарплата повинна бути позитивним числом', salary)
            elif salary > 1000000:
                result.add_error('salary', 'Зарплата не може перевищувати 1,000,000', salary)

        if result.errors:
            result.is_valid = False

        return result


# Utility functions for easy validation
def validate_email(email: str) -> ValidationResult:
    """Швидка валідація email"""
    validator = EmailValidator()
    return validator.validate(email)


def validate_phone(phone: Optional[str]) -> ValidationResult:
    """Швидка валідація телефону"""
    validator = PhoneValidator()
    return validator.validate(phone)


def validate_flight_data(flight_data: Dict[str, Any]) -> ValidationResult:
    """Швидка валідація даних рейсу"""
    validator = FlightValidator()
    return validator.validate(flight_data)


def validate_crew_data(crew_data: Dict[str, Any]) -> ValidationResult:
    """Швидка валідація даних екіпажу"""
    validator = CrewValidator()
    return validator.validate(crew_data)


def validate_datetime_range(departure: datetime, arrival: datetime) -> ValidationResult:
    """Швидка валідація діапазону дат"""
    validator = DateTimeValidator()
    return validator.validate_time_range(departure, arrival)


class CrewValidator(CrewValidator):
    """Розширений валідатор для членів екіпажу з додатковими методами"""

    def validate_crew_assignment(self, crew_data: Dict[str, Any], flight_data: Dict[str, Any]) -> ValidationResult:
        """Валідувати призначення члена екіпажу на рейс"""
        result = ValidationResult()

        # Спочатку валідуємо базові дані
        crew_result = self.validate(crew_data)
        result.errors.extend(crew_result.errors)

        if not crew_result.is_valid:
            result.is_valid = False
            return result

        position = crew_data.get('position')
        certification_level = crew_data.get('certification_level')
        years_experience = crew_data.get('years_experience', 0)
        aircraft_type = flight_data.get('aircraft_type')

        # Правила для різних позицій
        if position == 'PILOT':
            if certification_level not in ['SENIOR', 'CAPTAIN']:
                result.add_error('certification_level', 'Пілот повинен мати рівень SENIOR або CAPTAIN',
                                 certification_level)
            if years_experience < 3:
                result.add_error('years_experience', 'Пілот повинен мати мінімум 3 роки досвіду', years_experience)

        elif position == 'CO_PILOT':
            if years_experience < 1:
                result.add_error('years_experience', 'Другий пілот повинен мати мінімум 1 рік досвіду',
                                 years_experience)

        elif position == 'FLIGHT_ATTENDANT':
            if certification_level == 'JUNIOR' and years_experience < 1:
                result.add_error('years_experience', 'Стюард/стюардеса рівня JUNIOR повинен мати мінімум 1 рік досвіду',
                                 years_experience)

        # Перевірка сертифікації для типу літака
        if aircraft_type and aircraft_type.startswith('Boeing'):
            # Логіка перевірки сертифікації для Boeing
            pass
        elif aircraft_type and aircraft_type.startswith('Airbus'):
            # Логіка перевірки сертифікації для Airbus
            pass

        return result

    def validate_crew_list(self, crew_list: List[Dict[str, Any]], flight_data: Dict[str, Any]) -> ValidationResult:
        """Валідувати список екіпажу для рейсу"""
        result = ValidationResult()

        if not crew_list:
            result.add_error('crew_list', 'Список екіпажу не може бути пустим', crew_list)
            return result

        crew_required = flight_data.get('crew_required', 4)
        if len(crew_list) != crew_required:
            result.add_error('crew_list', f'Кількість членів екіпажу повинна дорівнювати {crew_required}',
                             len(crew_list))

        # Перевірка унікальності ID
        employee_ids = [crew.get('employee_id') for crew in crew_list]
        if len(employee_ids) != len(set(employee_ids)):
            result.add_error('crew_list', 'ID співробітників повинні бути унікальними', employee_ids)

        # Перевірка наявності обов'язкових ролей
        positions = [crew.get('position') for crew in crew_list]

        if 'PILOT' not in positions:
            result.add_error('crew_list', 'В екіпажі повинен бути щонайменше один пілот', positions)

        # Для великих літаків потрібен другий пілот
        aircraft_type = flight_data.get('aircraft_type', '')
        if any(big_plane in aircraft_type for big_plane in
               ['Boeing 747', 'Boeing 777', 'Boeing 787', 'Airbus A330', 'Airbus A340', 'Airbus A350']):
            if 'CO_PILOT' not in positions:
                result.add_error('crew_list', 'Для великих літаків потрібен другий пілот', positions)

        # Валідація кожного члена екіпажу
        for i, crew_member in enumerate(crew_list):
            member_result = self.validate_crew_assignment(crew_member, flight_data)
            for error in member_result.errors:
                result.add_error(f'crew_member_{i}_{error.field}', error.message, error.value)

        if result.errors:
            result.is_valid = False

        return result