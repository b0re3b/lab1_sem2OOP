"""
Сервіс для управління рейсами авіакомпанії
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from repositories.flight_repository import FlightRepository
from repositories.assignment_repository import AssignmentRepository
from models.flight import Flight
from utils.validators import FlightValidator, ValidationError
from utils.mappers import FlightMapper
from utils.decorators import log_execution, handle_exceptions, validate_input
from config.logging_config import log_info, log_error, log_warning


class FlightService:
    """Сервіс для управління рейсами"""

    def __init__(self):
        self.flight_repository = FlightRepository()
        self.assignment_repository = AssignmentRepository()
        self.flight_mapper = FlightMapper()
        self.validator = FlightValidator()

    @log_execution
    @handle_exceptions
    @validate_input
    def create_flight(self, flight_data: Dict[str, Any], created_by: int) -> Flight:
        """
        Створити новий рейс

        Args:
            flight_data: Дані рейсу
            created_by: ID користувача який створює рейс

        Returns:
            Flight: Створений рейс

        Raises:
            ValidationError: При невалідних даних
        """
        log_info(f"Creating new flight: {flight_data.get('flight_number')}")

        # Валідація даних рейсу
        self.validator.validate_flight_data(flight_data)

        # Перевірка унікальності номера рейсу
        existing_flight = self.flight_repository.find_by_flight_number(
            flight_data['flight_number']
        )
        if existing_flight:
            raise ValidationError(f"Рейс з номером {flight_data['flight_number']} вже існує")

        # Валідація часу рейсу
        departure_time = flight_data['departure_time']
        arrival_time = flight_data['arrival_time']

        if isinstance(departure_time, str):
            departure_time = datetime.fromisoformat(departure_time)
        if isinstance(arrival_time, str):
            arrival_time = datetime.fromisoformat(arrival_time)

        if departure_time >= arrival_time:
            raise ValidationError("Час відправлення має бути раніше часу прибуття")

        if departure_time <= datetime.now():
            raise ValidationError("Час відправлення має бути в майбутньому")

        # Додавання created_by до даних
        flight_data['created_by'] = created_by

        # Створення рейсу в БД
        flight_id = self.flight_repository.create_flight(flight_data)

        # Отримання створеного рейсу
        created_flight = self.flight_repository.find_by_id(flight_id)

        log_info(f"Flight created successfully: {flight_data['flight_number']} (ID: {flight_id})")

        return self.flight_mapper.from_db_row(created_flight)

    @log_execution
    @handle_exceptions
    def get_flight_by_id(self, flight_id: int) -> Optional[Flight]:
        """
        Отримати рейс за ID

        Args:
            flight_id: ID рейсу

        Returns:
            Optional[Flight]: Рейс або None
        """
        flight_row = self.flight_repository.find_by_id(flight_id)
        if not flight_row:
            return None

        return self.flight_mapper.from_db_row(flight_row)

    @log_execution
    @handle_exceptions
    def get_flight_by_number(self, flight_number: str) -> Optional[Flight]:
        """
        Отримати рейс за номером

        Args:
            flight_number: Номер рейсу

        Returns:
            Optional[Flight]: Рейс або None
        """
        flight_row = self.flight_repository.find_by_flight_number(flight_number)
        if not flight_row:
            return None

        return self.flight_mapper.from_db_row(flight_row)

    @log_execution
    @handle_exceptions
    def get_flights_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Flight]:
        """
        Отримати рейси за діапазоном дат

        Args:
            start_date: Початкова дата
            end_date: Кінцева дата

        Returns:
            List[Flight]: Список рейсів
        """
        if start_date >= end_date:
            raise ValidationError("Початкова дата має бути раніше кінцевої")

        flight_rows = self.flight_repository.find_all_by_date_range(start_date, end_date)

        return [self.flight_mapper.from_db_row(row) for row in flight_rows]

    @log_execution
    @handle_exceptions
    def get_flights_by_status(self, status: str) -> List[Flight]:
        """
        Отримати рейси за статусом

        Args:
            status: Статус рейсу

        Returns:
            List[Flight]: Список рейсів
        """
        valid_statuses = ['SCHEDULED', 'DELAYED', 'CANCELLED', 'COMPLETED']
        if status not in valid_statuses:
            raise ValidationError(f"Невалідний статус: {status}")

        flight_rows = self.flight_repository.find_all_by_status(status)

        return [self.flight_mapper.from_db_row(row) for row in flight_rows]

    @log_execution
    @handle_exceptions
    def get_flights_needing_crew(self) -> List[Flight]:
        """
        Отримати рейси які потребують призначення екіпажу

        Returns:
            List[Flight]: Список рейсів
        """
        flight_rows = self.flight_repository.find_flights_needing_crew()

        return [self.flight_mapper.from_db_row(row) for row in flight_rows]

    @log_execution
    @handle_exceptions
    @validate_input
    def update_flight(self, flight_id: int, update_data: Dict[str, Any]) -> Flight:
        """
        Оновити дані рейсу

        Args:
            flight_id: ID рейсу
            update_data: Дані для оновлення

        Returns:
            Flight: Оновлений рейс

        Raises:
            ValidationError: При невалідних даних
        """
        log_info(f"Updating flight ID: {flight_id}")

        # Перевірка існування рейсу
        existing_flight = self.flight_repository.find_by_id(flight_id)
        if not existing_flight:
            raise ValidationError(f"Рейс з ID {flight_id} не знайдено")

        # Валідація даних оновлення
        if 'flight_number' in update_data:
            other_flight = self.flight_repository.find_by_flight_number(
                update_data['flight_number']
            )
            if other_flight and other_flight[0] != flight_id:
                raise ValidationError(f"Рейс з номером {update_data['flight_number']} вже існує")

        # Валідація часу рейсу якщо оновлюється
        if 'departure_time' in update_data or 'arrival_time' in update_data:
            departure_time = update_data.get('departure_time', existing_flight[4])
            arrival_time = update_data.get('arrival_time', existing_flight[5])

            if isinstance(departure_time, str):
                departure_time = datetime.fromisoformat(departure_time)
            if isinstance(arrival_time, str):
                arrival_time = datetime.fromisoformat(arrival_time)

            if departure_time >= arrival_time:
                raise ValidationError("Час відправлення має бути раніше часу прибуття")

        # Оновлення в БД
        success = self.flight_repository.update_flight(flight_id, update_data)
        if not success:
            raise ValueError("Помилка при оновленні рейсу")

        # Отримання оновленого рейсу
        updated_flight = self.flight_repository.find_by_id(flight_id)

        log_info(f"Flight updated successfully: ID {flight_id}")

        return self.flight_mapper.from_db_row(updated_flight)

    @log_execution
    @handle_exceptions
    def update_flight_status(self, flight_id: int, new_status: str, reason: str = None) -> Flight:
        """
        Оновити статус рейсу

        Args:
            flight_id: ID рейсу
            new_status: Новий статус
            reason: Причина зміни статусу

        Returns:
            Flight: Оновлений рейс
        """
        log_info(f"Updating flight status: ID {flight_id}, new status: {new_status}")

        valid_statuses = ['SCHEDULED', 'DELAYED', 'CANCELLED', 'COMPLETED']
        if new_status not in valid_statuses:
            raise ValidationError(f"Невалідний статус: {new_status}")

        # Перевірка існування рейсу
        existing_flight = self.flight_repository.find_by_id(flight_id)
        if not existing_flight:
            raise ValidationError(f"Рейс з ID {flight_id} не знайдено")

        current_status = existing_flight[7]  # status field

        # Логіка переходів статусів
        valid_transitions = {
            'SCHEDULED': ['DELAYED', 'CANCELLED', 'COMPLETED'],
            'DELAYED': ['SCHEDULED', 'CANCELLED', 'COMPLETED'],
            'CANCELLED': [],  # Скасований рейс не можна змінити
            'COMPLETED': []   # Завершений рейс не можна змінити
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(
                f"Неможливо змінити статус з {current_status} на {new_status}"
            )

        # Оновлення статусу
        success = self.flight_repository.update_flight_status(flight_id, new_status)
        if not success:
            raise ValueError("Помилка при оновленні статусу рейсу")

        # Якщо рейс скасовано, скасувати всі призначення екіпажу
        if new_status == 'CANCELLED':
            assignments = self.assignment_repository.find_by_flight_id(flight_id)
            for assignment in assignments:
                self.assignment_repository.update_assignment_status(
                    assignment[0], 'CANCELLED'
                )
            log_warning(f"Cancelled all crew assignments for flight {flight_id}")

        # Отримання оновленого рейсу
        updated_flight = self.flight_repository.find_by_id(flight_id)

        log_info(f"Flight status updated: ID {flight_id}, status: {new_status}")

        return self.flight_mapper.from_db_row(updated_flight)

    @log_execution
    @handle_exceptions
    def delete_flight(self, flight_id: int) -> bool:
        """
        Видалити рейс

        Args:
            flight_id: ID рейсу

        Returns:
            bool: True якщо успішно видалено
        """
        log_info(f"Deleting flight: ID {flight_id}")

        # Перевірка існування рейсу
        existing_flight = self.flight_repository.find_by_id(flight_id)
        if not existing_flight:
            raise ValidationError(f"Рейс з ID {flight_id} не знайдено")

        # Перевірка чи є призначення екіпажу
        assignments = self.assignment_repository.find_by_flight_id(flight_id)
        if assignments:
            raise ValidationError(
                "Не можна видалити рейс з призначеним екіпажем. "
                "Спочатку скасуйте всі призначення."
            )

        # Видалення рейсу
        success = self.flight_repository.delete_flight(flight_id)

        if success:
            log_info(f"Flight deleted successfully: ID {flight_id}")
        else:
            log_error(f"Failed to delete flight: ID {flight_id}")

        return success

    @log_execution
    @handle_exceptions
    def get_flight_crew_summary(self, flight_id: int) -> Dict[str, Any]:
        """
        Отримати зведення по екіпажу рейсу

        Args:
            flight_id: ID рейсу

        Returns:
            Dict: Зведення по екіпажу
        """
        flight = self.get_flight_by_id(flight_id)
        if not flight:
            raise ValidationError(f"Рейс з ID {flight_id} не знайдено")

        assignments = self.assignment_repository.find_by_flight_id(flight_id)
        assigned_count = len([a for a in assignments if a[4] == 'ASSIGNED'])  # status field

        return {
            'flight_id': flight_id,
            'flight_number': flight.flight_number,
            'crew_required': flight.crew_required,
            'crew_assigned': assigned_count,
            'is_fully_staffed': assigned_count >= flight.crew_required,
            'assignments': assignments
        }

    @log_execution
    @handle_exceptions
    def get_daily_flight_schedule(self, date: datetime) -> List[Dict[str, Any]]:
        """
        Отримати розклад рейсів на день

        Args:
            date: Дата

        Returns:
            List[Dict]: Розклад рейсів
        """
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        flights = self.get_flights_by_date_range(start_date, end_date)

        schedule = []
        for flight in flights:
            crew_summary = self.get_flight_crew_summary(flight.id)

            schedule.append({
                'flight': flight,
                'crew_status': {
                    'required': crew_summary['crew_required'],
                    'assigned': crew_summary['crew_assigned'],
                    'is_ready': crew_summary['is_fully_staffed']
                }
            })

        # Сортування за часом відправлення
        schedule.sort(key=lambda x: x['flight'].departure_time)

        return schedule