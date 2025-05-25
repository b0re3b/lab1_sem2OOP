"""
Сервіс управління рейсами.
Містить бізнес-логіку для створення, оновлення та управління рейсами.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from . import CrewService
from ..models.flight import Flight, FlightStatus
from ..models.user import User
from ..repositories.assignment_repository import AssignmentRepository
from ..repositories.flight_repository import FlightRepository
from ..utils.decorators import audit_operation
from ..utils.validators import FlightValidator

logger = logging.getLogger(__name__)


class FlightValidationError(Exception):
    """Виняток для помилок валідації рейсів"""
    pass


class FlightConflictError(Exception):
    """Виняток для конфліктів рейсів"""
    pass


class FlightService:
    """Сервіс для управління рейсами авіакомпанії"""

    def __init__(
            self,
            flight_repository: FlightRepository,
            assignment_repository: AssignmentRepository,
            notification_service=None
    ):
        self.repository = flight_repository
        self.assignment_repository = assignment_repository
        self.notification_service = notification_service
        self.validator = FlightValidator()
        self.logger = logger
        self.crewserv = CrewService()
    # Основні CRUD операції

    def create(self, flight_data: Dict[str, Any], user_id: Optional[int] = None) -> Flight:
        """Створення нового рейсу"""
        try:
            self._validate_create_data(flight_data)

            flight = self.repository.create(flight_data)
            self._post_create_processing(flight, user_id)

            self.logger.info(f"Створено рейс {flight.flight_number} (ID: {flight.id})")
            return flight

        except Exception as e:
            self.logger.error(f"Помилка створення рейсу: {e}")
            raise

    def get_by_id(self, flight_id: int) -> Optional[Flight]:
        """Отримання рейсу за ID"""
        return  self.repository.get_by_id(flight_id)

    def get_all(self) -> List[Flight]:
        """Отримання всіх рейсів"""
        return  self.repository.get_all()

    def update(self, flight_id: int, update_data: Dict[str, Any], user_id: Optional[int] = None) -> Optional[Flight]:
        """Оновлення рейсу"""
        try:
            existing_flight =  self.get_by_id(flight_id)
            if not existing_flight:
                raise FlightValidationError(f"Рейс з ID {flight_id} не знайдено")

            old_flight_data = existing_flight.to_dict()
            self._validate_update_data(flight_id, update_data, existing_flight)

            updated_flight = self.repository.update(flight_id, update_data)
            if updated_flight:
                old_flight = Flight.from_dict(old_flight_data)
                self._post_update_processing(updated_flight, old_flight, user_id)

            self.logger.info(f"Оновлено рейс {flight_id}")
            return updated_flight

        except Exception as e:
            self.logger.error(f"Помилка оновлення рейсу {flight_id}: {e}")
            raise

    def delete(self, flight_id: int, user_id: Optional[int] = None) -> bool:
        """Видалення рейсу"""
        try:
            existing_flight = self.get_by_id(flight_id)
            if not existing_flight:
                return False

            self._validate_delete(flight_id, existing_flight)
            self._pre_delete_processing(existing_flight, user_id)

            result = self.repository.delete(flight_id)
            if result:
                self._post_delete_processing(existing_flight, user_id)

            self.logger.info(f"Видалено рейс {flight_id}")
            return result

        except Exception as e:
            self.logger.error(f"Помилка видалення рейсу {flight_id}: {e}")
            raise

    async def count(self) -> int:
        """Підрахунок кількості рейсів"""
        return await self.model.count()

    # Валідація

    def _validate_create_data(self, entity_data: Dict[str, Any]) -> None:
        """Валідація даних перед створенням рейсу"""
        validation_result = self.validator.validate(entity_data)
        if not validation_result.is_valid:
            raise FlightValidationError(f"Помилки валідації: {', '.join(validation_result.get_error_messages())}")

        existing_flight = self.repository.get_by_flight_number(entity_data['flight_number'])
        if existing_flight:
            raise FlightConflictError(f"Рейс з номером {entity_data['flight_number']} вже існує")

        self._check_aircraft_conflicts(entity_data)

    def _validate_update_data(self, entity_id: int, update_data: Dict[str, Any], existing_entity: Flight) -> None:
        """Валідація даних перед оновленням рейсу"""
        if update_data:
            validation_result = self.validator.validate(update_data)
            if not validation_result.is_valid:
                raise FlightValidationError(f"Помилки валідації: {', '.join(validation_result.get_error_messages())}")

        if existing_entity.status == FlightStatus.COMPLETED:
            raise FlightValidationError("Неможливо змінити завершений рейс")

        if any(key in update_data for key in ['departure_time', 'arrival_time', 'aircraft_type']):
            merged_data = {**existing_entity.to_dict(), **update_data}
            self._check_aircraft_conflicts(merged_data)

    def _validate_delete(self, entity_id: int, existing_entity: Flight) -> None:
        """Валідація перед видаленням рейсу"""
        if existing_entity.status == FlightStatus.COMPLETED:
            raise FlightValidationError("Неможливо видалити завершений рейс")

    # Обробка подій

    def _post_create_processing(self, entity: Flight, user_id: Optional[int] = None) -> None:
        """Обробка після створення рейсу"""
        if not entity.status:
            self.repository.update(entity.id, {'status': FlightStatus.SCHEDULED})

        if user_id and self.notification_service:
            user = self._get_user_by_id(user_id)
            if user:
                self.notification_service.notify_flight_created(entity, user)

        self._log_business_event('flight_created', entity.id, {
            'flight_number': entity.flight_number,
            'aircraft_type': entity.aircraft_type
        }, user_id)

    def _post_update_processing(self, updated_entity: Flight, old_entity: Flight, user_id: Optional[int] = None) -> None:
        """Обробка після оновлення рейсу"""
        if user_id and self.notification_service:
            user = self._get_user_by_id(user_id)
            if user:
                self.notification_service.notify_flight_updated(updated_entity, user)

        self.crewserv._log_business_event('flight_updated', updated_entity.id, {
            'flight_number': updated_entity.flight_number,
            'changes': self._get_entity_changes(old_entity, updated_entity)
        }, user_id)

    def _pre_delete_processing(self, entity: Flight, user_id: Optional[int] = None) -> None:
        """Обробка перед видаленням рейсу"""
        self.assignment_repository.cancel_assignments_by_flight(entity.id)

    def _post_delete_processing(self, entity: Flight, user_id: Optional[int] = None) -> None:
        """Обробка після видалення рейсу"""
        self._log_business_event('flight_deleted', entity.id, {
            'flight_number': entity.flight_number
        }, user_id)

    # Спеціалізовані методи для рейсів

    def create_flight(self, flight_data: Dict[str, Any], created_by: User) -> Flight:
        """Створення нового рейсу з користувачем"""
        flight_data['created_by_id'] = created_by.id
        return  self.create(flight_data, created_by.id)

    def update_flight(self, flight_id: int, update_data: Dict[str, Any], updated_by: User) -> Optional[Flight]:
        """Оновлення рейсу з користувачем"""
        return  self.update(flight_id, update_data, updated_by.id)

    def get_flight_by_number(self, flight_number: str) -> Optional[Flight]:
        """Отримання рейсу за номером"""
        return  self.repository.get_by_flight_number(flight_number)

    def get_flights_by_status(self, status: FlightStatus) -> List[Flight]:
        """Отримання рейсів за статусом"""
        return  self.repository.get_flights_by_status(status)

    def get_flights_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Flight]:
        """Отримання рейсів за діапазоном дат"""
        return  self.repository.get_flights_by_date_range(start_date, end_date)

    def get_today_flights(self) -> List[Flight]:
        """Отримання рейсів на сьогодні"""
        return  self.repository.get_today_flights()

    def get_upcoming_flights(self, days: int = 7) -> List[Flight]:
        """Отримання майбутніх рейсів"""
        return  self.repository.get_upcoming_flights(days)

    @audit_operation
    def update_flight_status(self, flight_id: int, new_status: FlightStatus, updated_by: User) -> Flight:
        """Оновлення статусу рейсу"""
        try:
            flight =  self.get_by_id(flight_id)
            if not flight:
                raise FlightValidationError(f"Рейс з ID {flight_id} не знайдено")

            if not self._is_valid_status_transition(flight.status, new_status):
                raise FlightValidationError(
                    f"Неможливо змінити статус з {flight.status.value} на {new_status.value}"
                )

            updated_flight =  self.repository.update_flight_status(flight_id, new_status)

            if self.notification_service:
                self.notification_service.notify_flight_status_changed(updated_flight, updated_by)

            self._log_business_event('status_changed', flight_id, {
                'old_status': flight.status.value,
                'new_status': new_status.value
            }, updated_by.id)

            return updated_flight

        except Exception as e:
            self.logger.error(f"Помилка зміни статусу рейсу {flight_id}: {e}")
            raise

    @audit_operation
    def cancel_flight(self, flight_id: int, reason: str, cancelled_by: User) -> Flight:
        """Скасування рейсу"""
        try:
            flight =  self.get_by_id(flight_id)
            if not flight:
                raise FlightValidationError(f"Рейс з ID {flight_id} не знайдено")

            cancelled_flight =  self.repository.cancel_flight(flight_id, reason)
            self.assignment_repository.cancel_assignments_by_flight(flight_id)

            if self.notification_service:
                 self.notification_service.notify_flight_cancelled(cancelled_flight, reason, cancelled_by)

            self._log_business_event('flight_cancelled', flight_id, {
                'flight_number': flight.flight_number,
                'reason': reason
            }, cancelled_by.id)

            return cancelled_flight

        except Exception as e:
            self.logger.error(f"Помилка скасування рейсу {flight_id}: {e}")
            raise

    def search_flights(self, search_criteria: Dict[str, Any]) -> List[Flight]:
        """Пошук рейсів за критеріями"""
        return  self.repository.search_flights(search_criteria)

    def get_flight_statistics(self) -> Dict[str, Any]:
        """Отримання статистики рейсів"""
        try:
            stats =  self.repository.get_flight_statistics()
            total_flights =  self.count()

            result = {
                'total_flights': total_flights,
                'by_status': stats.get('by_status', {}),
                'staffing_summary':  self._get_staffing_summary(),
                'upcoming_flights': len( self.get_upcoming_flights()),
                'today_flights': len( self.get_today_flights())
            }

            return result

        except Exception as e:
            self.logger.error(f"Помилка отримання статистики рейсів: {e}")
            return {}

    def get_flights_requiring_attention(self) -> List[Flight]:
        """Отримання рейсів, які потребують уваги"""
        try:
            attention_flights = []

            understaffed =  self.repository.get_understaffed_flights()
            attention_flights.extend(understaffed)

            delayed =  self.get_flights_by_status(FlightStatus.DELAYED)
            attention_flights.extend(delayed)

            today_flights =  self.get_today_flights()
            for flight in today_flights:
                if not flight.is_fully_staffed():
                    attention_flights.append(flight)

            unique_flights = {f.id: f for f in attention_flights}
            return list(unique_flights.values())

        except Exception as e:
            self.logger.error(f"Помилка отримання рейсів, які потребують уваги: {e}")
            return []

    def check_flight_readiness(self, flight_id: int) -> Dict[str, Any]:
        """Перевірка готовності рейсу до виконання"""
        try:
            flight =  self.get_by_id(flight_id)
            if not flight:
                return {'ready': False, 'errors': ['Рейс не знайдено']}

            errors = []
            warnings = []

            if flight.status == FlightStatus.CANCELLED:
                errors.append('Рейс скасовано')

            if not flight.is_fully_staffed():
                errors.append('Екіпаж не повністю укомплектований')

            departure_time = flight.departure_time
            if departure_time:
                time_until_departure = departure_time - datetime.now()

                if time_until_departure.total_seconds() < 0:
                    errors.append('Час вільоту вже минув')
                elif time_until_departure.total_seconds() < 7200:
                    warnings.append(f'Залишилось {int(time_until_departure.total_seconds() / 3600)} год до вильоту')

            assignments = self.assignment_repository.get_assignments_by_flight(flight_id)
            if not assignments:
                errors.append('Відсутні призначення екіпажу')

            for assignment in assignments:
                if assignment.has_conflicts:
                    warnings.append(f'Конфлікт у розкладі члена екіпажу {assignment.crew_member.name}')

            if not flight.aircraft_type:
                errors.append('Не вказано тип літака')

            if not flight.departure_airport or not flight.arrival_airport:
                errors.append('Не вказано повний маршрут рейсу')

            return {
                'ready': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'flight_number': flight.flight_number,
                'status': flight.status.value,
                'departure_time': departure_time.isoformat() if departure_time else None,
                'crew_status': 'complete' if flight.is_fully_staffed() else 'incomplete'
            }

        except Exception as e:
            self.logger.error(f"Помилка перевірки готовності рейсу {flight_id}: {e}")
            return {
                'ready': False,
                'errors': ['Внутрішня помилка системи'],
                'warnings': []
            }

    def get_flight_crew_requirements(self, flight_id: int) -> Dict[str, Any]:
        """Отримання вимог до екіпажу для рейсу"""
        try:
            flight =  self.get_by_id(flight_id)
            if not flight:
                return {}

            aircraft_requirements = {
                'Boeing-737': {'pilots': 2, 'flight_attendants': 3, 'engineers': 1},
                'Airbus-A320': {'pilots': 2, 'flight_attendants': 3, 'engineers': 1},
                'Boeing-777': {'pilots': 2, 'flight_attendants': 6, 'engineers': 2},
                'Airbus-A380': {'pilots': 3, 'flight_attendants': 12, 'engineers': 2}
            }

            base_requirements = aircraft_requirements.get(
                flight.aircraft_type,
                {'pilots': 2, 'flight_attendants': 3, 'engineers': 1}
            )

            current_assignments =  self.assignment_repository.get_assignments_by_flight(flight_id)
            current_crew = {'pilots': 0, 'flight_attendants': 0, 'engineers': 0}

            for assignment in current_assignments:
                role = assignment.crew_member.role.lower()
                if 'pilot' in role:
                    current_crew['pilots'] += 1
                elif 'attendant' in role or 'стюард' in role:
                    current_crew['flight_attendants'] += 1
                elif 'engineer' in role or 'інженер' in role:
                    current_crew['engineers'] += 1

            requirements = {}
            for role, required in base_requirements.items():
                requirements[role] = {
                    'required': required,
                    'current': current_crew.get(role, 0),
                    'needed': max(0, required - current_crew.get(role, 0))
                }

            return {
                'flight_number': flight.flight_number,
                'aircraft_type': flight.aircraft_type,
                'requirements': requirements,
                'is_fully_staffed': all(req['needed'] == 0 for req in requirements.values())
            }

        except Exception as e:
            self.logger.error(f"Помилка отримання вимог до екіпажу рейсу {flight_id}: {e}")
            return {}

    def bulk_update_flights(self, flight_ids: List[int], update_data: Dict[str, Any], updated_by: User) -> List[Flight]:
        """Масове оновлення рейсів"""
        updated_flights = []

        for flight_id in flight_ids:
            try:
                updated_flight = self.update_flight(flight_id, update_data, updated_by)
                if updated_flight:
                    updated_flights.append(updated_flight)
            except Exception as e:
                self.logger.error(f"Помилка масового оновлення рейсу {flight_id}: {e}")
                continue

        return updated_flights

    def export_flights_data(self, search_criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """Експорт даних рейсів для звітів"""
        try:
            if search_criteria:
                flights = self.search_flights(search_criteria)
            else:
                flights = self.get_all()

            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_flights': len(flights),
                'flights': []
            }

            for flight in flights:
                crew_info = self.assignment_repository.get_assignments_by_flight(flight.id)

                flight_data = {
                    'flight_number': flight.flight_number,
                    'aircraft_type': flight.aircraft_type,
                    'departure_airport': flight.departure_airport,
                    'arrival_airport': flight.arrival_airport,
                    'departure_time': flight.departure_time.isoformat() if flight.departure_time else None,
                    'arrival_time': flight.arrival_time.isoformat() if flight.arrival_time else None,
                    'status': flight.status.value,
                    'crew_count': len(crew_info),
                    'is_fully_staffed': flight.is_fully_staffed(),
                    'created_at': flight.created_at.isoformat() if flight.created_at else None
                }

                export_data['flights'].append(flight_data)

            return export_data

        except Exception as e:
            self.logger.error(f"Помилка експорту даних рейсів: {e}")
            return {'error': str(e)}

    # Допоміжні методи

    def _check_aircraft_conflicts(self, flight_data: Dict[str, Any]) -> None:
        """Перевірка конфліктів використання літака"""
        aircraft_type = flight_data.get('aircraft_type')
        departure_time = flight_data.get('departure_time')
        arrival_time = flight_data.get('arrival_time')

        if not all([aircraft_type, departure_time, arrival_time]):
            return

        conflicting_flights =  self.repository.get_flights_by_aircraft_type(
            aircraft_type, departure_time, arrival_time
        )

        if conflicting_flights:
            conflict_numbers = [f.flight_number for f in conflicting_flights]
            raise FlightConflictError(
                f"Конфлікт використання літака {aircraft_type} з рейсами: {', '.join(conflict_numbers)}"
            )

    def _is_valid_status_transition(self, current_status: FlightStatus, new_status: FlightStatus) -> bool:
        """Перевірка допустимості переходу між статусами"""
        valid_transitions = {
            FlightStatus.SCHEDULED: [FlightStatus.DELAYED, FlightStatus.CANCELLED, FlightStatus.COMPLETED],
            FlightStatus.DELAYED: [FlightStatus.SCHEDULED, FlightStatus.CANCELLED, FlightStatus.COMPLETED],
            FlightStatus.CANCELLED: [FlightStatus.SCHEDULED],
            FlightStatus.COMPLETED: []
        }

        return new_status in valid_transitions.get(current_status, [])

    def _get_staffing_summary(self) -> Dict[str, int]:
        """Отримання підсумку укомплектованості рейсів"""
        try:
            fully_staffed =  self.repository.get_fully_staffed_flights()
            understaffed =  self.repository.get_understaffed_flights()

            return {
                'fully_staffed': len(fully_staffed),
                'understaffed': len(understaffed),
                'not_staffed': 0
            }

        except Exception as e:
            self.logger.warning(f"Помилка отримання підсумку укомплектованості: {e}")
            return {'fully_staffed': 0, 'understaffed': 0, 'not_staffed': 0}

    def _get_entity_changes(self, old_entity: Flight, new_entity: Flight) -> Dict[str, Any]:
        """Отримання змін між сутностями"""
        changes = {}
        fields_to_compare = ['flight_number', 'aircraft_type', 'departure_time', 'arrival_time', 'status']

        for field in fields_to_compare:
            old_value = getattr(old_entity, field, None)
            new_value = getattr(new_entity, field, None)

            if old_value != new_value:
                changes[field] = {
                    'old': str(old_value) if old_value else None,
                    'new': str(new_value) if new_value else None
                }

        return changes

