from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.crew_member import CrewMember, CertificationLevel
from ..models.flight_assignment import AssignmentStatus
from ..repositories.assignment_repository import AssignmentRepository
from ..repositories.crew_repository import CrewRepository
from ..repositories.flight_repository import FlightRepository
from ..utils.decorators import log_execution_time, audit_operation
from ..utils.mappers import CrewMemberMapper, CrewMemberDTO
from ..utils.validators import CrewValidator, ValidationError


class CrewService:

    def __init__(self):
        self.crew_repo = CrewRepository()
        self.assignment_repo = assignment_repository
        self.flight_repo = flight_repository
        self.db_session = db_session
        self.validator = CrewValidator()
        self.mapper = CrewMemberMapper()
        self.logger = logging.getLogger(__name__)

    # CRUD операції

    @log_execution_time
    @audit_operation
    async def create_crew_member(self, crew_data: Dict[str, Any], user_id: Optional[int] = None) -> CrewMember:
        """Створення нового члена екіпажу"""
        try:
            # Валідація даних
            await self._validate_create_data(crew_data)

            # Створення через репозиторій
            crew_member = await self.crew_repo.create(crew_data)

            # Пост-обробка
            await self._post_create_processing(crew_member, user_id)

            return crew_member

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in create_crew_member: {str(e)}")
            await self.db_session.rollback()
            raise RuntimeError(f"Помилка створення члена екіпажу: {str(e)}")

    @log_execution_time
    async def get_crew_member_by_id(self, crew_id: int) -> Optional[CrewMember]:
        """Отримання члена екіпажу за ID"""
        try:
            return await self.crew_repo.get_by_id(crew_id)
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_crew_member_by_id: {str(e)}")
            raise RuntimeError(f"Помилка отримання члена екіпажу: {str(e)}")

    @log_execution_time
    async def get_all_crew_members(self, skip: int = 0, limit: int = 100) -> List[CrewMember]:
        """Отримання всіх членів екіпажу з пагінацією"""
        try:
            return await self.crew_repo.get_all(skip=skip, limit=limit)
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_all_crew_members: {str(e)}")
            raise RuntimeError(f"Помилка отримання списку екіпажу: {str(e)}")

    @log_execution_time
    @audit_operation
    async def update_crew_member(
        self,
        crew_id: int,
        update_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Optional[CrewMember]:
        """Оновлення інформації про члена екіпажу"""
        try:
            # Отримання існуючого запису
            existing_crew = await self.crew_repo.get_by_id(crew_id)
            if not existing_crew:
                raise ValueError(f"Член екіпажу з ID {crew_id} не знайдено")

            # Валідація даних для оновлення
            await self._validate_update_data(crew_id, update_data, existing_crew)

            # Оновлення через репозиторій
            updated_crew = await self.crew_repo.update(crew_id, update_data)

            # Пост-обробка
            if updated_crew:
                await self._post_update_processing(updated_crew, update_data, user_id)

            return updated_crew

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in update_crew_member: {str(e)}")
            await self.db_session.rollback()
            raise RuntimeError(f"Помилка оновлення члена екіпажу: {str(e)}")

    @log_execution_time
    @audit_operation
    async def delete_crew_member(self, crew_id: int, user_id: Optional[int] = None) -> bool:
        """Видалення члена екіпажу"""
        try:
            # Отримання існуючого запису
            existing_crew = await self.crew_repo.get_by_id(crew_id)
            if not existing_crew:
                raise ValueError(f"Член екіпажу з ID {crew_id} не знайдено")

            # Валідація перед видаленням
            await self._validate_delete(crew_id, existing_crew)

            # Видалення через репозиторій
            success = await self.crew_repo.delete(crew_id)

            # Пост-обробка
            if success:
                await self._post_delete_processing(existing_crew, user_id)

            return success

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in delete_crew_member: {str(e)}")
            await self.db_session.rollback()
            raise RuntimeError(f"Помилка видалення члена екіпажу: {str(e)}")

    # Методи валідації

    async def _validate_create_data(self, entity_data: Dict[str, Any]) -> None:
        """Валідація даних перед створенням члена екіпажу"""
        # Валідація через спеціалізований валідатор
        validation_result = self.validator.validate(entity_data)
        if not validation_result.is_valid:
            raise ValidationError("Некоректні дані члена екіпажу", validation_result.errors)

        # Перевірка унікальності employee_id
        if await self.crew_repo.get_by_employee_id(entity_data['employee_id']):
            raise ValueError(f"Співробітник з ID {entity_data['employee_id']} вже існує")

    async def _validate_update_data(
        self,
        entity_id: int,
        update_data: Dict[str, Any],
        existing_entity: CrewMember
    ) -> None:
        """Валідація даних перед оновленням"""
        validation_result = self.validator.validate(update_data, is_update=True)
        if not validation_result.is_valid:
            raise ValidationError("Некоректні дані для оновлення", validation_result.errors)

        # Перевірка унікальності employee_id при оновленні
        if 'employee_id' in update_data:
            existing_with_employee_id = await self.crew_repo.get_by_employee_id(update_data['employee_id'])
            if existing_with_employee_id and existing_with_employee_id.id != entity_id:
                raise ValueError(f"Співробітник з ID {update_data['employee_id']} вже існує")

    async def _validate_delete(self, entity_id: int, existing_entity: CrewMember) -> None:
        """Валідація перед видаленням члена екіпажу"""
        # Перевірка активних призначень
        active_assignments = await self.assignment_repo.get_assignments_by_crew_member(
            entity_id, status=AssignmentStatus.ASSIGNED
        )
        if active_assignments:
            flights = []
            for assignment in active_assignments:
                flight = await self.flight_repo.get_by_id(assignment.flight_id)
                if flight:
                    flights.append(flight.flight_number)

            if flights:
                raise ValueError(
                    f"Неможливо видалити члена екіпажу. "
                    f"Призначений на рейси: {', '.join(flights)}"
                )

    # Методи пост-обробки

    async def _post_create_processing(self, entity: CrewMember, user_id: Optional[int] = None) -> None:
        """Обробка після створення члена екіпажу"""
        await self._log_business_event(
            "CREATE",
            entity.id,
            {"description": f"Створено члена екіпажу: {entity.full_name}"},
            user_id
        )

    async def _post_update_processing(
        self,
        entity: CrewMember,
        update_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> None:
        """Обробка після оновлення члена екіпажу"""
        await self._log_business_event(
            "UPDATE",
            entity.id,
            {
                "description": f"Оновлено члена екіпажу: {entity.full_name}",
                "updated_fields": list(update_data.keys())
            },
            user_id
        )

    async def _post_delete_processing(self, entity: CrewMember, user_id: Optional[int] = None) -> None:
        """Обробка після видалення члена екіпажу"""
        await self._log_business_event(
            "DELETE",
            entity.id,
            {"description": f"Видалено члена екіпажу: {entity.full_name}"},
            user_id
        )

    # Специфічні методи для роботи з екіпажем

    @log_execution_time
    async def get_available_crew(self, flight_id: int) -> List[CrewMemberDTO]:
        """Отримання доступного екіпажу для рейсу"""
        flight = await self.flight_repo.get_by_id(flight_id)
        if not flight:
            raise ValueError(f"Рейс з ID {flight_id} не знайдено")

        # Отримання доступного екіпажу
        available_crew = await self.crew_repo.get_available_crew(
            departure_time=flight.departure_time,
            arrival_time=flight.arrival_time
        )

        return self.mapper.to_list_dto(available_crew)

    @log_execution_time
    async def get_crew_by_position(self, position: str) -> List[CrewMemberDTO]:
        """Отримання екіпажу за посадою"""
        crew_members = await self.crew_repo.get_by_position(position)
        return self.mapper.to_list_dto(crew_members)

    @log_execution_time
    async def get_captains(self) -> List[CrewMemberDTO]:
        """Отримання всіх капітанів"""
        captains = await self.crew_repo.get_captains()
        return self.mapper.to_list_dto(captains)

    @log_execution_time
    async def get_senior_crew(self) -> List[CrewMemberDTO]:
        """Отримання старшого екіпажу"""
        senior_crew = await self.crew_repo.get_senior_crew()
        return self.mapper.to_list_dto(senior_crew)

    @log_execution_time
    @audit_operation
    async def set_crew_availability(
        self,
        crew_id: int,
        is_available: bool,
        user_id: Optional[int] = None
    ) -> bool:
        """Встановлення доступності члена екіпажу"""
        crew_member = await self.get_crew_member_by_id(crew_id)
        if not crew_member:
            raise ValueError(f"Член екіпажу з ID {crew_id} не знайдено")

        try:
            # Перевірка активних призначень при встановленні недоступності
            if not is_available:
                active_assignments = await self.assignment_repo.get_assignments_by_crew_member(
                    crew_id, status=AssignmentStatus.ASSIGNED
                )
                if active_assignments:
                    flights = []
                    for assignment in active_assignments:
                        flight = await self.flight_repo.get_by_id(assignment.flight_id)
                        if flight:
                            flights.append(flight.flight_number)

                    if flights:
                        raise ValueError(
                            f"Неможливо встановити недоступність. "
                            f"Член екіпажу призначений на рейси: {', '.join(flights)}"
                        )

            # Оновлення доступності
            success = await self.crew_repo.set_availability(crew_id, is_available)

            if success:
                status = "доступний" if is_available else "недоступний"
                await self._log_business_event(
                    "UPDATE_AVAILABILITY",
                    crew_id,
                    {"description": f"Змінено статус доступності на '{status}'"},
                    user_id
                )

            return success

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in set_crew_availability: {str(e)}")
            raise RuntimeError(f"Помилка оновлення доступності: {str(e)}")

    @log_execution_time
    @audit_operation
    async def promote_crew_member(
        self,
        crew_id: int,
        new_level: CertificationLevel,
        user_id: Optional[int] = None
    ) -> bool:
        """Підвищення кваліфікації члена екіпажу"""
        crew_member = await self.get_crew_member_by_id(crew_id)
        if not crew_member:
            raise ValueError(f"Член екіпажу з ID {crew_id} не знайдено")

        old_level = crew_member.certification_level

        # Перевірка валідності підвищення
        if not self._is_valid_promotion(old_level, new_level):
            raise ValueError(f"Некоректне підвищення з {old_level.value} до {new_level.value}")

        try:
            success = await self.crew_repo.promote_crew_member(crew_id, new_level)

            if success:
                await self._log_business_event(
                    "PROMOTION",
                    crew_id,
                    {"description": f"Підвищено з {old_level.value} до {new_level.value}"},
                    user_id
                )

            return success

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in promote_crew_member: {str(e)}")
            raise RuntimeError(f"Помилка підвищення кваліфікації: {str(e)}")

    @log_execution_time
    async def get_crew_statistics(self) -> Dict[str, Any]:
        """Отримання статистики екіпажу"""
        stats = await self.crew_repo.get_crew_statistics()

        # Додаткова статистика
        total_crew = stats.get('total_crew', 0)
        available_crew = stats.get('available_crew', 0)
        unavailable_crew = total_crew - available_crew

        return {
            **stats,
            'unavailable_crew': unavailable_crew,
            'availability_rate': (available_crew / total_crew * 100) if total_crew > 0 else 0,
            'captain_ratio': (stats.get('captains', 0) / total_crew * 100) if total_crew > 0 else 0,
            'senior_ratio': (stats.get('senior_crew', 0) / total_crew * 100) if total_crew > 0 else 0
        }

    @log_execution_time
    async def get_crew_workload_report(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Отримання звіту про навантаження екіпажу"""
        return await self.crew_repo.get_crew_workload_report(start_date, end_date)

    @log_execution_time
    async def search_crew_members(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[CrewMemberDTO]:
        """Пошук членів екіпажу"""
        crew_members = await self.crew_repo.search_crew_members(query, filters or {})
        return self.mapper.to_list_dto(crew_members)

    @log_execution_time
    async def validate_crew_for_flight(self, flight_id: int, crew_ids: List[int]) -> Dict[str, Any]:
        """Валідація екіпажу для рейсу"""
        flight = await self.flight_repo.get_by_id(flight_id)
        if not flight:
            raise ValueError(f"Рейс з ID {flight_id} не знайдено")

        crew_members = []
        for crew_id in crew_ids:
            crew_member = await self.get_crew_member_by_id(crew_id)
            if crew_member:
                crew_members.append(crew_member)

        # Валідація екіпажу
        validation_result = await self.validator.validate_crew_assignment(flight, crew_members)

        return {
            'is_valid': validation_result.is_valid,
            'errors': validation_result.errors,
            'warnings': validation_result.get('warnings', []),
            'crew_composition': self._analyze_crew_composition(crew_members)
        }

    # Допоміжні методи

    def _is_valid_promotion(self, old_level: CertificationLevel, new_level: CertificationLevel) -> bool:
        """Перевірка валідності підвищення кваліфікації"""
        promotion_rules = {
            CertificationLevel.JUNIOR: [CertificationLevel.SENIOR],
            CertificationLevel.SENIOR: [CertificationLevel.CAPTAIN],
            CertificationLevel.CAPTAIN: []  # Капітан - найвищий рівень
        }

        return new_level in promotion_rules.get(old_level, [])

    def _analyze_crew_composition(self, crew_members: List[CrewMember]) -> Dict[str, Any]:
        """Аналіз складу екіпажу"""
        positions = {}
        certification_levels = {level.value: 0 for level in CertificationLevel}

        for crew_member in crew_members:
            # Підрахунок позицій
            position_name = crew_member.crew_position.position_name if crew_member.crew_position else "Unknown"
            positions[position_name] = positions.get(position_name, 0) + 1

            # Підрахунок рівнів кваліфікації
            certification_levels[crew_member.certification_level.value] += 1

        return {
            'total_crew': len(crew_members),
            'positions': positions,
            'certification_levels': certification_levels,
            'has_captain': any(cm.is_captain for cm in crew_members),
            'senior_count': sum(1 for cm in crew_members if cm.is_senior)
        }

    # Зручні методи для створення та конвертації DTO

    async def create_crew_member_dto(self, crew_data: Dict[str, Any], created_by: int) -> CrewMemberDTO:
        """Створення нового члена екіпажу з поверненням DTO"""
        crew_member = await self.create_crew_member(crew_data, created_by)
        return self.mapper.to_dto(crew_member)

    async def get_crew_member_dto(self, crew_id: int) -> Optional[CrewMemberDTO]:
        """Отримання члена екіпажу у форматі DTO"""
        crew_member = await self.get_crew_member_by_id(crew_id)
        return self.mapper.to_dto(crew_member) if crew_member else None

    async def get_all_crew_dto(self, skip: int = 0, limit: int = 100) -> List[CrewMemberDTO]:
        """Отримання всіх членів екіпажу у форматі DTO"""
        crew_members = await self.get_all_crew_members(skip=skip, limit=limit)
        return self.mapper.to_list_dto(crew_members)

    # Методи для логування та аудиту

    async def _log_business_event(
        self,
        operation: str,
        entity_id: int,
        details: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> None:
        """Логування бізнес-подій"""
        log_entry = {
            'timestamp': datetime.now(),
            'operation': operation,
            'entity_type': 'CrewMember',
            'entity_id': entity_id,
            'user_id': user_id,
            'details': details
        }

        self.logger.info(f"Business event: {log_entry}")



    # Методи валідації бізнес-правил

    async def _validate_availability_change(self, data: Dict[str, Any]) -> None:
        """Валідація зміни доступності"""
        crew_id = data.get('crew_id')
        is_available = data.get('is_available')

        if not is_available and crew_id:
            active_assignments = await self.assignment_repo.get_assignments_by_crew_member(
                crew_id, status=AssignmentStatus.ASSIGNED
            )
            if active_assignments:
                raise ValidationError("Неможливо встановити недоступність для члена екіпажу з активними призначеннями")

