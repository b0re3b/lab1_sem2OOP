from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..models.flight_assignment import FlightAssignment
from ..models.crew_member import CrewMember
from ..repositories.assignment_repository import AssignmentRepository
from ..repositories.crew_repository import CrewRepository
from ..repositories.flight_repository import FlightRepository
from ..utils.validators import AssignmentValidator, ValidationError
from ..utils.mappers import FlightAssignmentMapper
from ..config.logging_config import log_info, log_error, log_warning

logger = logging.getLogger(__name__)


class AssignmentService:
    """Сервіс для управління призначеннями екіпажу на рейси"""

    def __init__(self):
        self.assignment_repository = AssignmentRepository()
        self.crew_repository = CrewRepository()
        self.flight_repository = FlightRepository()
        self.assignment_mapper = FlightAssignmentMapper()
        self.validator = AssignmentValidator()

    def create_assignment(self, assignment_data: Dict[str, Any], assigned_by_user_id: int) -> FlightAssignment:
        """
        Створення нового призначення екіпажу на рейс

        Args:
            assignment_data: Дані призначення
            assigned_by_user_id: ID користувача, який створює призначення

        Returns:
            FlightAssignment: Створене призначення

        Raises:
            ValidationError: При невалідних даних
            ValueError: При бізнес-логічних помилках
        """
        try:
            # Валідація вхідних даних
            self.validator.validate_assignment_data(assignment_data)

            flight_id = assignment_data.get('flight_id')
            crew_member_id = assignment_data.get('crew_member_id')

            # Перевірка існування рейсу та члена екіпажу
            flight = self.flight_repository.find_by_id(flight_id)
            if not flight:
                raise ValueError(f"Рейс з ID {flight_id} не знайдено")

            crew_member = self.crew_repository.find_by_id(crew_member_id)
            if not crew_member:
                raise ValueError(f"Член екіпажу з ID {crew_member_id} не знайдено")

            # Перевірка доступності члена екіпажу
            if not crew_member.is_available:
                raise ValueError(f"Член екіпажу {crew_member.first_name} {crew_member.last_name} недоступний")

            # Перевірка конфліктів розкладу
            if not self._check_schedule_conflicts(crew_member_id, flight.departure_time, flight.arrival_time):
                raise ValueError("Член екіпажу вже призначений на інший рейс у цей час")

            # Перевірка, чи не перевищено максимальну кількість екіпажу для рейсу
            current_assignments = self.assignment_repository.find_by_flight_id(flight_id)
            if len(current_assignments) >= flight.crew_required * 2:  # Максимум у 2 рази більше необхідного
                raise ValueError("Перевищено максимальну кількість екіпажу для рейсу")

            # Додавання системних полів
            assignment_data['assigned_by'] = assigned_by_user_id
            assignment_data['assigned_at'] = datetime.now()
            assignment_data['status'] = assignment_data.get('status', 'ASSIGNED')

            # Створення призначення
            assignment_id = self.assignment_repository.create_assignment(assignment_data)
            created_assignment = self.assignment_repository.find_by_id(assignment_id)

            log_info(f"Створено призначення {assignment_id} для екіпажу {crew_member_id} на рейс {flight_id}")

            return created_assignment

        except ValidationError as e:
            log_error(f"Помилка валідації при створенні призначення: {str(e)}")
            raise
        except Exception as e:
            log_error(f"Помилка при створенні призначення: {str(e)}")
            raise

    def get_assignment_by_id(self, assignment_id: int) -> Optional[FlightAssignment]:
        """Отримання призначення за ID"""
        try:
            assignment = self.assignment_repository.find_by_id(assignment_id)
            if assignment:
                log_info(f"Знайдено призначення {assignment_id}")
            return assignment
        except Exception as e:
            log_error(f"Помилка при отриманні призначення {assignment_id}: {str(e)}")
            raise

    def get_assignments_by_flight(self, flight_id: int) -> List[FlightAssignment]:
        """Отримання всіх призначень для рейсу"""
        try:
            assignments = self.assignment_repository.find_by_flight_id(flight_id)
            log_info(f"Знайдено {len(assignments)} призначень для рейсу {flight_id}")
            return assignments
        except Exception as e:
            log_error(f"Помилка при отриманні призначень для рейсу {flight_id}: {str(e)}")
            raise

    def get_assignments_by_crew_member(self, crew_member_id: int) -> List[FlightAssignment]:
        """Отримання всіх призначень для члена екіпажу"""
        try:
            assignments = self.assignment_repository.find_by_crew_member_id(crew_member_id)
            log_info(f"Знайдено {len(assignments)} призначень для члена екіпажу {crew_member_id}")
            return assignments
        except Exception as e:
            log_error(f"Помилка при отриманні призначень для члена екіпажу {crew_member_id}: {str(e)}")
            raise

    def get_assignments_by_date_range(self, start_date: datetime, end_date: datetime) -> List[FlightAssignment]:
        """Отримання призначень за період"""
        try:
            assignments = self.assignment_repository.find_by_date_range(start_date, end_date)
            log_info(f"Знайдено {len(assignments)} призначень за період {start_date} - {end_date}")
            return assignments
        except Exception as e:
            log_error(f"Помилка при отриманні призначень за період: {str(e)}")
            raise

    def update_assignment(self, assignment_id: int, update_data: Dict[str, Any]) -> FlightAssignment:
        """
        Оновлення призначення

        Args:
            assignment_id: ID призначення
            update_data: Дані для оновлення

        Returns:
            FlightAssignment: Оновлене призначення
        """
        try:
            # Перевірка існування призначення
            existing_assignment = self.assignment_repository.find_by_id(assignment_id)
            if not existing_assignment:
                raise ValueError(f"Призначення з ID {assignment_id} не знайдено")

            # Валідація даних оновлення
            allowed_fields = ['status', 'notes']
            filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}

            if 'status' in filtered_data:
                if filtered_data['status'] not in ['ASSIGNED', 'CONFIRMED', 'CANCELLED']:
                    raise ValidationError("Невалідний статус призначення")

            # Оновлення
            self.assignment_repository.update_assignment(assignment_id, filtered_data)
            updated_assignment = self.assignment_repository.find_by_id(assignment_id)

            log_info(f"Оновлено призначення {assignment_id}")

            return updated_assignment

        except ValidationError as e:
            log_error(f"Помилка валідації при оновленні призначення {assignment_id}: {str(e)}")
            raise
        except Exception as e:
            log_error(f"Помилка при оновленні призначення {assignment_id}: {str(e)}")
            raise

    def cancel_assignment(self, assignment_id: int, reason: str = None) -> bool:
        """
        Скасування призначення

        Args:
            assignment_id: ID призначення
            reason: Причина скасування

        Returns:
            bool: True якщо успішно скасовано
        """
        try:
            existing_assignment = self.assignment_repository.find_by_id(assignment_id)
            if not existing_assignment:
                raise ValueError(f"Призначення з ID {assignment_id} не знайдено")

            if existing_assignment.status == 'CANCELLED':
                raise ValueError("Призначення вже скасовано")

            update_data = {
                'status': 'CANCELLED',
                'notes': reason or 'Скасовано без вказання причини'
            }

            self.assignment_repository.update_assignment_status(assignment_id, 'CANCELLED')
            if reason:
                self.assignment_repository.update_assignment(assignment_id, {'notes': reason})

            log_info(f"Скасовано призначення {assignment_id}. Причина: {reason}")

            return True

        except Exception as e:
            log_error(f"Помилка при скасуванні призначення {assignment_id}: {str(e)}")
            raise

    def delete_assignment(self, assignment_id: int) -> bool:
        """
        Видалення призначення

        Args:
            assignment_id: ID призначення

        Returns:
            bool: True якщо успішно видалено
        """
        try:
            existing_assignment = self.assignment_repository.find_by_id(assignment_id)
            if not existing_assignment:
                raise ValueError(f"Призначення з ID {assignment_id} не знайдено")

            # Перевірка чи можна видаляти (наприклад, тільки скасовані або майбутні)
            flight = self.flight_repository.find_by_id(existing_assignment.flight_id)
            if flight and flight.departure_time <= datetime.now():
                raise ValueError("Неможливо видалити призначення для рейсу, що вже відбувся або відбувається")

            self.assignment_repository.delete_assignment(assignment_id)

            log_info(f"Видалено призначення {assignment_id}")

            return True

        except Exception as e:
            log_error(f"Помилка при видаленні призначення {assignment_id}: {str(e)}")
            raise

    def get_all_assignments(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """
        Отримання всіх призначень з пагінацією

        Args:
            page: Номер сторінки
            per_page: Кількість записів на сторінку

        Returns:
            Dict з даними та метаінформацією
        """
        try:
            offset = (page - 1) * per_page
            assignments = self.assignment_repository.get_all_assignments(limit=per_page, offset=offset)

            # Отримання загальної кількості для пагінації
            total_count = len(self.assignment_repository.get_all_assignments())

            log_info(f"Отримано {len(assignments)} призначень (сторінка {page})")

            return {
                'assignments': assignments,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                }
            }

        except Exception as e:
            log_error(f"Помилка при отриманні списку призначень: {str(e)}")
            raise

    def get_flight_crew_statistics(self, flight_id: int) -> Dict[str, Any]:
        """Отримання статистики екіпажу для рейсу"""
        try:
            stats = self.assignment_repository.get_flight_crew_statistics(flight_id)
            log_info(f"Отримано статистику екіпажу для рейсу {flight_id}")
            return stats
        except Exception as e:
            log_error(f"Помилка при отриманні статистики для рейсу {flight_id}: {str(e)}")
            raise

    def get_crew_member_workload(self, crew_member_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Отримання навантаження члена екіпажу за період"""
        try:
            workload = self.assignment_repository.get_crew_member_workload(crew_member_id, start_date, end_date)
            log_info(f"Отримано навантаження для члена екіпажу {crew_member_id}")
            return workload
        except Exception as e:
            log_error(f"Помилка при отриманні навантаження для члена екіпажу {crew_member_id}: {str(e)}")
            raise

    def get_available_crew_for_flight(self, flight_id: int) -> List[CrewMember]:
        """
        Отримання доступного екіпажу для рейсу

        Args:
            flight_id: ID рейсу

        Returns:
            List[CrewMember]: Список доступних членів екіпажу
        """
        try:
            flight = self.flight_repository.find_by_id(flight_id)
            if not flight:
                raise ValueError(f"Рейс з ID {flight_id} не знайдено")

            # Отримання всіх доступних членів екіпажу
            available_crew = self.crew_repository.find_available_for_flight(
                flight.departure_time,
                flight.arrival_time
            )

            # Фільтрування тих, хто вже призначений на цей рейс
            current_assignments = self.assignment_repository.find_by_flight_id(flight_id)
            assigned_crew_ids = {assignment.crew_member_id for assignment in current_assignments
                                 if assignment.status in ['ASSIGNED', 'CONFIRMED']}

            available_crew = [crew for crew in available_crew
                              if crew.id not in assigned_crew_ids]

            log_info(f"Знайдено {len(available_crew)} доступних членів екіпажу для рейсу {flight_id}")

            return available_crew

        except Exception as e:
            log_error(f"Помилка при отриманні доступного екіпажу для рейсу {flight_id}: {str(e)}")
            raise

    def auto_assign_crew(self, flight_id: int, assigned_by_user_id: int) -> List[FlightAssignment]:
        """
        Автоматичне призначення екіпажу на рейс

        Args:
            flight_id: ID рейсу
            assigned_by_user_id: ID користувача, який призначає

        Returns:
            List[FlightAssignment]: Список створених призначень
        """
        try:
            flight = self.flight_repository.find_by_id(flight_id)
            if not flight:
                raise ValueError(f"Рейс з ID {flight_id} не знайдено")

            # Перевірка чи рейс потребує екіпажу
            current_assignments = self.assignment_repository.find_by_flight_id(flight_id)
            active_assignments = [a for a in current_assignments if a.status in ['ASSIGNED', 'CONFIRMED']]

            if len(active_assignments) >= flight.crew_required:
                log_warning(f"Рейс {flight_id} вже має достатньо екіпажу")
                return active_assignments

            # Отримання доступного екіпажу
            available_crew = self.get_available_crew_for_flight(flight_id)

            if not available_crew:
                raise ValueError("Немає доступного екіпажу для автоматичного призначення")

            # Групування за посадами
            crew_by_position = {}
            for crew_member in available_crew:
                position_name = crew_member.position_name if hasattr(crew_member, 'position_name') else 'UNKNOWN'
                if position_name not in crew_by_position:
                    crew_by_position[position_name] = []
                crew_by_position[position_name].append(crew_member)

            # Пріоритетний порядок призначення посад
            priority_positions = ['PILOT', 'CO_PILOT', 'NAVIGATOR', 'RADIO_OPERATOR', 'FLIGHT_ATTENDANT']

            created_assignments = []
            needed_crew = flight.crew_required - len(active_assignments)

            for position in priority_positions:
                if needed_crew <= 0:
                    break

                if position in crew_by_position and crew_by_position[position]:
                    # Сортування за досвідом (спочатку більш досвідчені)
                    crew_by_position[position].sort(
                        key=lambda x: (x.experience_years, x.certification_level == 'CAPTAIN'),
                        reverse=True
                    )

                    crew_member = crew_by_position[position][0]

                    assignment_data = {
                        'flight_id': flight_id,
                        'crew_member_id': crew_member.id,
                        'status': 'ASSIGNED',
                        'notes': f'Автоматично призначено ({position})'
                    }

                    assignment = self.create_assignment(assignment_data, assigned_by_user_id)
                    created_assignments.append(assignment)
                    needed_crew -= 1

            log_info(f"Автоматично створено {len(created_assignments)} призначень для рейсу {flight_id}")

            return created_assignments

        except Exception as e:
            log_error(f"Помилка при автоматичному призначенні екіпажу для рейсу {flight_id}: {str(e)}")
            raise

    def _check_schedule_conflicts(self, crew_member_id: int, departure_time: datetime, arrival_time: datetime) -> bool:
        """
        Перевірка конфліктів розкладу для члена екіпажу

        Args:
            crew_member_id: ID члена екіпажу
            departure_time: Час відправлення рейсу
            arrival_time: Час прибуття рейсу

        Returns:
            bool: True якщо немає конфліктів
        """
        try:
            return self.assignment_repository._check_crew_availability(
                crew_member_id, departure_time, arrival_time
            )
        except Exception as e:
            log_error(f"Помилка при перевірці конфліктів розкладу: {str(e)}")
            return False

    def get_assignment_summary(self) -> Dict[str, Any]:
        """Отримання загальної інформації про призначення"""
        try:
            all_assignments = self.assignment_repository.get_all_assignments()

            summary = {
                'total_assignments': len(all_assignments),
                'by_status': {},
                'recent_assignments': 0
            }

            # Статистика за статусами
            for assignment in all_assignments:
                status = assignment.status
                summary['by_status'][status] = summary['by_status'].get(status, 0) + 1

            # Призначення за останні 7 днів
            week_ago = datetime.now() - timedelta(days=7)
            summary['recent_assignments'] = len([
                a for a in all_assignments
                if a.assigned_at and a.assigned_at >= week_ago
            ])

            log_info("Отримано загальну інформацію про призначення")

            return summary

        except Exception as e:
            log_error(f"Помилка при отриманні загальної інформації: {str(e)}")
            raise