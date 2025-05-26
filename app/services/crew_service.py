"""
Сервіс для роботи з екіпажем
Реалізує бізнес-логіку управління членами екіпажу та їх посадами
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models import CrewMember
from app.models.crew_position import CrewPosition
from app.repositories import CrewRepository
from app.utils.validators import CrewValidator, ValidationError
from app.utils.mappers import CrewMemberMapper, CrewPositionMapper
from app.utils.decorators import LoggingDecorators, ErrorHandlingDecorators, ValidationDecorators
from app.config.logging_config import log_info, log_error, log_warning


class CrewService:
    """
    Сервіс для управління екіпажем авіакомпанії
    """
    log_execution = LoggingDecorators.log_execution
    handle_exceptions = ErrorHandlingDecorators.handle_exceptions
    validate_input = ValidationDecorators.validate_input
    def __init__(self):
        self.crew_repository = CrewRepository()
        self.crew_validator = CrewValidator()
        self.crew_member_mapper = CrewMemberMapper()
        self.crew_position_mapper = CrewPositionMapper()
        self.log_execution = LoggingDecorators.log_execution
        self.handle_exceptions = ErrorHandlingDecorators.handle_exceptions
        self.validate_input = ValidationDecorators.validate_input

    @log_execution
    @handle_exceptions
    @validate_input
    def create_crew_member(self, crew_data: Dict[str, Any], created_by_user_id: int) -> CrewMember:
        """
        Створення нового члена екіпажу

        Args:
            crew_data: Дані про члена екіпажу
            created_by_user_id: ID користувача, який створює запис

        Returns:
            CrewMember: Створений член екіпажу

        Raises:
            ValidationError: При невалідних даних
        """
        log_info(f"Creating new crew member by user {created_by_user_id}")

        # Валідація даних
        self.crew_validator.validate_crew_member_data(crew_data)

        # Перевірка унікальності employee_id
        existing_member = self.crew_repository.find_by_employee_id(crew_data.get('employee_id'))
        if existing_member:
            raise ValidationError(f"Crew member with employee_id {crew_data.get('employee_id')} already exists")

        # Перевірка існування позиції
        position = self.crew_repository.find_position_by_id(crew_data.get('position_id'))
        if not position:
            raise ValidationError(f"Position with id {crew_data.get('position_id')} does not exist")

        # Створення члена екіпажу
        crew_member_id = self.crew_repository.create_crew_member(crew_data)
        created_member = self.crew_repository.find_by_id(crew_member_id)

        log_info(f"Successfully created crew member with id {crew_member_id}")
        return self.crew_member_mapper.from_db_row(created_member)

    @log_execution
    @handle_exceptions
    def get_crew_member_by_id(self, crew_member_id: int) -> Optional[CrewMember]:
        """
        Отримання члена екіпажу за ID

        Args:
            crew_member_id: ID члена екіпажу

        Returns:
            Optional[CrewMember]: Член екіпажу або None
        """
        crew_member_data = self.crew_repository.find_by_id(crew_member_id)
        if not crew_member_data:
            return None

        return self.crew_member_mapper.from_db_row(crew_member_data)

    @log_execution
    @handle_exceptions
    def get_crew_member_by_employee_id(self, employee_id: str) -> Optional[CrewMember]:
        """
        Отримання члена екіпажу за службовим номером

        Args:
            employee_id: Службовий номер

        Returns:
            Optional[CrewMember]: Член екіпажу або None
        """
        crew_member_data = self.crew_repository.find_by_employee_id(employee_id)
        if not crew_member_data:
            return None

        return self.crew_member_mapper.from_db_row(crew_member_data)

    @log_execution
    @handle_exceptions
    def get_available_crew_by_position(self, position_id: int) -> List[CrewMember]:
        """
        Отримання доступних членів екіпажу за позицією

        Args:
            position_id: ID позиції

        Returns:
            List[CrewMember]: Список доступних членів екіпажу
        """
        crew_members_data = self.crew_repository.find_available_by_position(position_id)
        return [self.crew_member_mapper.from_db_row(data) for data in crew_members_data]

    @log_execution
    @handle_exceptions
    def get_available_crew_for_flight(self, flight_id: int, departure_time: datetime, arrival_time: datetime) -> List[
        CrewMember]:
        """
        Отримання доступних членів екіпажу для конкретного рейсу

        Args:
            flight_id: ID рейсу
            departure_time: Час відльоту
            arrival_time: Час прильоту

        Returns:
            List[CrewMember]: Список доступних членів екіпажу
        """
        crew_members_data = self.crew_repository.find_available_for_flight(flight_id, departure_time, arrival_time)
        return [self.crew_member_mapper.from_db_row(data) for data in crew_members_data]

    @log_execution
    @handle_exceptions
    @validate_input
    def update_crew_member(self, crew_member_id: int, update_data: Dict[str, Any], updated_by_user_id: int) -> Optional[
        CrewMember]:
        """
        Оновлення даних члена екіпажу

        Args:
            crew_member_id: ID члена екіпажу
            update_data: Дані для оновлення
            updated_by_user_id: ID користувача, який оновлює

        Returns:
            Optional[CrewMember]: Оновлений член екіпажу або None
        """
        log_info(f"Updating crew member {crew_member_id} by user {updated_by_user_id}")

        # Перевірка існування члена екіпажу
        existing_member = self.crew_repository.find_by_id(crew_member_id)
        if not existing_member:
            log_warning(f"Crew member with id {crew_member_id} not found")
            return None

        # Валідація даних для оновлення
        if update_data:
            # Часткова валідація тільки тих полів, які оновлюються
            filtered_data = {k: v for k, v in update_data.items() if v is not None}
            if filtered_data:
                self.crew_validator.validate_crew_member_data(filtered_data, partial=True)

        # Перевірка унікальності employee_id, якщо він оновлюється
        if 'employee_id' in update_data and update_data['employee_id'] != existing_member.get('employee_id'):
            existing_with_employee_id = self.crew_repository.find_by_employee_id(update_data['employee_id'])
            if existing_with_employee_id:
                raise ValidationError(f"Crew member with employee_id {update_data['employee_id']} already exists")

        # Оновлення
        success = self.crew_repository.update_crew_member(crew_member_id, update_data)
        if not success:
            log_error(f"Failed to update crew member {crew_member_id}")
            return None

        # Отримання оновлених даних
        updated_member_data = self.crew_repository.find_by_id(crew_member_id)
        log_info(f"Successfully updated crew member {crew_member_id}")
        return self.crew_member_mapper.from_db_row(updated_member_data)

    @log_execution
    @handle_exceptions
    def set_crew_availability(self, crew_member_id: int, is_available: bool, updated_by_user_id: int) -> bool:
        """
        Встановлення доступності члена екіпажу

        Args:
            crew_member_id: ID члена екіпажу
            is_available: Статус доступності
            updated_by_user_id: ID користувача, який змінює статус

        Returns:
            bool: Успішність операції
        """
        log_info(f"Setting crew member {crew_member_id} availability to {is_available} by user {updated_by_user_id}")

        # Перевірка існування члена екіпажу
        existing_member = self.crew_repository.find_by_id(crew_member_id)
        if not existing_member:
            log_warning(f"Crew member with id {crew_member_id} not found")
            return False

        success = self.crew_repository.set_availability(crew_member_id, is_available)
        if success:
            log_info(f"Successfully updated availability for crew member {crew_member_id}")
        else:
            log_error(f"Failed to update availability for crew member {crew_member_id}")

        return success

    @log_execution
    @handle_exceptions
    def get_all_positions(self) -> List[CrewPosition]:
        """
        Отримання всіх позицій екіпажу

        Returns:
            List[CrewPosition]: Список позицій
        """
        positions_data = self.crew_repository.get_all_positions()
        return [self.crew_position_mapper.from_db_row(data) for data in positions_data]

    @log_execution
    @handle_exceptions
    def get_position_by_id(self, position_id: int) -> Optional[CrewPosition]:
        """
        Отримання позиції за ID

        Args:
            position_id: ID позиції

        Returns:
            Optional[CrewPosition]: Позиція або None
        """
        position_data = self.crew_repository.find_position_by_id(position_id)
        if not position_data:
            return None

        return self.crew_position_mapper.from_db_row(position_data)

    @log_execution
    @handle_exceptions
    def get_crew_workload_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Отримання статистики навантаження екіпажу

        Args:
            start_date: Початкова дата
            end_date: Кінцева дата

        Returns:
            Dict[str, Any]: Статистика навантаження
        """
        log_info(f"Getting crew workload statistics from {start_date} to {end_date}")



        statistics = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'total_crew_members': len(self.crew_repository.find_available_by_position(None)),  # Всі активні
            'crew_by_position': {},
            'workload_analysis': {
                'overloaded_crew': [],
                'underutilized_crew': [],
                'optimal_workload_crew': []
            }
        }

        # Збір статистики по позиціям
        positions = self.get_all_positions()
        for position in positions:
            crew_in_position = self.get_available_crew_by_position(position.id)
            statistics['crew_by_position'][position.position_name] = {
                'total_members': len(crew_in_position),
                'available_members': len([c for c in crew_in_position if c.is_available])
            }

        return statistics

    @log_execution
    @handle_exceptions
    def check_crew_member_availability(self, crew_member_id: int, start_time: datetime, end_time: datetime) -> bool:
        """
        Перевірка доступності члена екіпажу на конкретний період

        Args:
            crew_member_id: ID члена екіпажу
            start_time: Початок періоду
            end_time: Кінець періоду

        Returns:
            bool: Чи доступний член екіпажу
        """
        # Перевірка базової доступності
        crew_member = self.get_crew_member_by_id(crew_member_id)
        if not crew_member or not crew_member.is_available:
            return False


        available_crew = self.get_available_crew_for_flight(None, start_time, end_time)
        return any(member.id == crew_member_id for member in available_crew)

    @log_execution
    @handle_exceptions
    def get_crew_recommendations_for_flight(self, flight_data: Dict[str, Any]) -> Dict[str, List[CrewMember]]:
        """
        Отримання рекомендацій екіпажу для рейсу

        Args:
            flight_data: Дані рейсу

        Returns:
            Dict[str, List[CrewMember]]: Рекомендації по позиціям
        """
        log_info(f"Getting crew recommendations for flight {flight_data.get('flight_number')}")

        departure_time = flight_data.get('departure_time')
        arrival_time = flight_data.get('arrival_time')
        aircraft_type = flight_data.get('aircraft_type', '')

        recommendations = {}
        positions = self.get_all_positions()

        for position in positions:
            available_crew = []
            if departure_time and arrival_time:
                # Отримуємо доступний екіпаж для цього часового періоду
                available_for_flight = self.get_available_crew_for_flight(
                    flight_data.get('id'), departure_time, arrival_time
                )
                available_crew = [
                    member for member in available_for_flight
                    if member.position_id == position.id
                ]
            else:
                # Якщо часи не вказані, беремо всіх доступних за позицією
                available_crew = self.get_available_crew_by_position(position.id)

            # Сортуємо за досвідом (найбільш досвідчені спочатку)
            available_crew.sort(key=lambda x: (x.experience_years, x.certification_level), reverse=True)

            recommendations[position.position_name] = available_crew[:5]  # Топ 5 кандидатів

        return recommendations

    def __del__(self):
        """Очищення ресурсів при знищенні об'єкта"""
        try:
            if hasattr(self, 'crew_repository'):
                del self.crew_repository
        except Exception as e:
            log_error(f"Error during CrewService cleanup: {e}")