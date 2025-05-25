from typing import Dict, List, Any, Optional, Type, TypeVar
from datetime import datetime
from models.user import User
from models.flight import Flight
from models.crew_member import CrewMember
from models.crew_position import CrewPosition
from models.flight_assignment import FlightAssignment
from models.log import OperationLog

T = TypeVar('T')


class BaseMapper:
    """Базовий клас для всіх маперів"""

    @staticmethod
    def safe_get(data: Dict, key: str, default: Any = None, converter: callable = None):
        """Безпечне отримання значення з словника з конвертацією"""
        value = data.get(key, default)
        if value is not None and converter:
            try:
                return converter(value)
            except (ValueError, TypeError):
                return default
        return value

    @staticmethod
    def timestamp_to_datetime(timestamp: Any) -> Optional[datetime]:
        """Конвертація timestamp в datetime"""
        if timestamp is None:
            return None
        if isinstance(timestamp, datetime):
            return timestamp
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                return None
        return None


class UserMapper(BaseMapper):
    """Мапер для користувачів"""

    @staticmethod
    def from_db_row(row: tuple, columns: List[str]) -> User:
        """Перетворення рядка з БД в модель User"""
        data = dict(zip(columns, row))
        return User(
            id=data.get('id'),
            keycloak_id=data.get('keycloak_id'),
            username=data.get('username'),
            email=data.get('email'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            role=data.get('role'),
            is_active=data.get('is_active', True),
            created_at=UserMapper.timestamp_to_datetime(data.get('created_at')),
            updated_at=UserMapper.timestamp_to_datetime(data.get('updated_at'))
        )

    @staticmethod
    def to_dict(user: User) -> Dict[str, Any]:
        """Перетворення моделі User в словник"""
        return {
            'id': user.id,
            'keycloak_id': user.keycloak_id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'full_name': f"{user.first_name} {user.last_name}"
        }

    @staticmethod
    def from_keycloak_data(keycloak_data: Dict[str, Any]) -> User:
        """Перетворення даних з Keycloak в модель User"""
        return User(
            keycloak_id=keycloak_data.get('sub'),
            username=keycloak_data.get('preferred_username'),
            email=keycloak_data.get('email'),
            first_name=keycloak_data.get('given_name', ''),
            last_name=keycloak_data.get('family_name', ''),
            role=UserMapper._extract_role_from_keycloak(keycloak_data),
            is_active=True
        )

    @staticmethod
    def _extract_role_from_keycloak(keycloak_data: Dict[str, Any]) -> str:
        """Витягує роль з даних Keycloak"""
        resource_access = keycloak_data.get('resource_access', {})
        airline_client = resource_access.get('airline-system', {})
        roles = airline_client.get('roles', [])

        if 'admin' in roles:
            return 'ADMIN'
        elif 'dispatcher' in roles:
            return 'DISPATCHER'
        else:
            return 'USER'


class FlightMapper(BaseMapper):
    """Мапер для рейсів"""

    @staticmethod
    def from_db_row(row: tuple, columns: List[str]) -> Flight:
        """Перетворення рядка з БД в модель Flight"""
        data = dict(zip(columns, row))
        return Flight(
            id=data.get('id'),
            flight_number=data.get('flight_number'),
            departure_city=data.get('departure_city'),
            arrival_city=data.get('arrival_city'),
            departure_time=FlightMapper.timestamp_to_datetime(data.get('departure_time')),
            arrival_time=FlightMapper.timestamp_to_datetime(data.get('arrival_time')),
            aircraft_type=data.get('aircraft_type'),
            status=data.get('status', 'SCHEDULED'),
            crew_required=data.get('crew_required', 4),
            created_by=data.get('created_by'),
            created_at=FlightMapper.timestamp_to_datetime(data.get('created_at')),
            updated_at=FlightMapper.timestamp_to_datetime(data.get('updated_at'))
        )

    @staticmethod
    def to_dict(flight: Flight) -> Dict[str, Any]:
        """Перетворення моделі Flight в словник"""
        return {
            'id': flight.id,
            'flight_number': flight.flight_number,
            'departure_city': flight.departure_city,
            'arrival_city': flight.arrival_city,
            'departure_time': flight.departure_time.isoformat() if flight.departure_time else None,
            'arrival_time': flight.arrival_time.isoformat() if flight.arrival_time else None,
            'aircraft_type': flight.aircraft_type,
            'status': flight.status,
            'crew_required': flight.crew_required,
            'created_by': flight.created_by,
            'created_at': flight.created_at.isoformat() if flight.created_at else None,
            'updated_at': flight.updated_at.isoformat() if flight.updated_at else None,
            'route': f"{flight.departure_city} → {flight.arrival_city}",
            'duration_minutes': FlightMapper._calculate_duration(flight.departure_time, flight.arrival_time)
        }

    @staticmethod
    def _calculate_duration(departure: datetime, arrival: datetime) -> Optional[int]:
        """Розрахунок тривалості рейсу в хвилинах"""
        if departure and arrival:
            return int((arrival - departure).total_seconds() / 60)
        return None


class CrewMemberMapper(BaseMapper):
    """Мапер для членів екіпажу"""

    @staticmethod
    def from_db_row(row: tuple, columns: List[str]) -> CrewMember:
        """Перетворення рядка з БД в модель CrewMember"""
        data = dict(zip(columns, row))
        return CrewMember(
            id=data.get('id'),
            employee_id=data.get('employee_id'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            position_id=data.get('position_id'),
            experience_years=data.get('experience_years', 0),
            certification_level=data.get('certification_level', 'JUNIOR'),
            is_available=data.get('is_available', True),
            phone=data.get('phone'),
            email=data.get('email'),
            created_at=CrewMemberMapper.timestamp_to_datetime(data.get('created_at')),
            updated_at=CrewMemberMapper.timestamp_to_datetime(data.get('updated_at'))
        )

    @staticmethod
    def to_dict(crew_member: CrewMember) -> Dict[str, Any]:
        """Перетворення моделі CrewMember в словник"""
        return {
            'id': crew_member.id,
            'employee_id': crew_member.employee_id,
            'first_name': crew_member.first_name,
            'last_name': crew_member.last_name,
            'position_id': crew_member.position_id,
            'experience_years': crew_member.experience_years,
            'certification_level': crew_member.certification_level,
            'is_available': crew_member.is_available,
            'phone': crew_member.phone,
            'email': crew_member.email,
            'created_at': crew_member.created_at.isoformat() if crew_member.created_at else None,
            'updated_at': crew_member.updated_at.isoformat() if crew_member.updated_at else None,
            'full_name': f"{crew_member.first_name} {crew_member.last_name}",
            'experience_level': CrewMemberMapper._get_experience_level(crew_member.experience_years)
        }

    @staticmethod
    def _get_experience_level(years: int) -> str:
        """Визначення рівня досвіду"""
        if years < 2:
            return 'Новачок'
        elif years < 5:
            return 'Досвідчений'
        elif years < 10:
            return 'Експерт'
        else:
            return 'Ветеран'


class CrewPositionMapper(BaseMapper):
    """Мапер для посад екіпажу"""

    @staticmethod
    def from_db_row(row: tuple, columns: List[str]) -> CrewPosition:
        """Перетворення рядка з БД в модель CrewPosition"""
        data = dict(zip(columns, row))
        return CrewPosition(
            id=data.get('id'),
            position_name=data.get('position_name'),
            description=data.get('description'),
            is_required=data.get('is_required', True),
            created_at=CrewPositionMapper.timestamp_to_datetime(data.get('created_at'))
        )

    @staticmethod
    def to_dict(position: CrewPosition) -> Dict[str, Any]:
        """Перетворення моделі CrewPosition в словник"""
        return {
            'id': position.id,
            'position_name': position.position_name,
            'description': position.description,
            'is_required': position.is_required,
            'created_at': position.created_at.isoformat() if position.created_at else None,
            'display_name': CrewPositionMapper._get_display_name(position.position_name)
        }

    @staticmethod
    def _get_display_name(position_name: str) -> str:
        """Отримання відображуваної назви посади"""
        names = {
            'PILOT': 'Пілот',
            'CO_PILOT': 'Другий пілот',
            'NAVIGATOR': 'Штурман',
            'RADIO_OPERATOR': 'Радист',
            'FLIGHT_ATTENDANT': 'Бортпровідник',
            'FLIGHT_ENGINEER': 'Бортінженер'
        }
        return names.get(position_name, position_name)


class FlightAssignmentMapper(BaseMapper):
    """Мапер для призначень екіпажу"""

    @staticmethod
    def from_db_row(row: tuple, columns: List[str]) -> FlightAssignment:
        """Перетворення рядка з БД в модель FlightAssignment"""
        data = dict(zip(columns, row))
        return FlightAssignment(
            id=data.get('id'),
            flight_id=data.get('flight_id'),
            crew_member_id=data.get('crew_member_id'),
            assigned_by=data.get('assigned_by'),
            assigned_at=FlightAssignmentMapper.timestamp_to_datetime(data.get('assigned_at')),
            status=data.get('status', 'ASSIGNED'),
            notes=data.get('notes')
        )

    @staticmethod
    def to_dict(assignment: FlightAssignment) -> Dict[str, Any]:
        """Перетворення моделі FlightAssignment в словник"""
        return {
            'id': assignment.id,
            'flight_id': assignment.flight_id,
            'crew_member_id': assignment.crew_member_id,
            'assigned_by': assignment.assigned_by,
            'assigned_at': assignment.assigned_at.isoformat() if assignment.assigned_at else None,
            'status': assignment.status,
            'notes': assignment.notes,
            'status_display': FlightAssignmentMapper._get_status_display(assignment.status)
        }

    @staticmethod
    def _get_status_display(status: str) -> str:
        """Отримання відображуваного статусу"""
        statuses = {
            'ASSIGNED': 'Призначено',
            'CONFIRMED': 'Підтверджено',
            'CANCELLED': 'Скасовано'
        }
        return statuses.get(status, status)


class OperationLogMapper(BaseMapper):
    """Мапер для логів операцій"""

    @staticmethod
    def from_db_row(row: tuple, columns: List[str]) -> OperationLog:
        """Перетворення рядка з БД в модель OperationLog"""
        data = dict(zip(columns, row))
        return OperationLog(
            id=data.get('id'),
            user_id=data.get('user_id'),
            operation_type=data.get('operation_type'),
            table_name=data.get('table_name'),
            record_id=data.get('record_id'),
            old_values=data.get('old_values'),
            new_values=data.get('new_values'),
            description=data.get('description'),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent'),
            created_at=OperationLogMapper.timestamp_to_datetime(data.get('created_at'))
        )

    @staticmethod
    def to_dict(log: OperationLog) -> Dict[str, Any]:
        """Перетворення моделі OperationLog в словник"""
        return {
            'id': log.id,
            'user_id': log.user_id,
            'operation_type': log.operation_type,
            'table_name': log.table_name,
            'record_id': log.record_id,
            'old_values': log.old_values,
            'new_values': log.new_values,
            'description': log.description,
            'ip_address': log.ip_address,
            'user_agent': log.user_agent,
            'created_at': log.created_at.isoformat() if log.created_at else None,
            'operation_display': OperationLogMapper._get_operation_display(log.operation_type)
        }

    @staticmethod
    def _get_operation_display(operation_type: str) -> str:
        """Отримання відображуваного типу операції"""
        operations = {
            'CREATE': 'Створення',
            'UPDATE': 'Оновлення',
            'DELETE': 'Видалення',
            'SELECT': 'Перегляд',
            'LOGIN': 'Вхід',
            'LOGOUT': 'Вихід'
        }
        return operations.get(operation_type, operation_type)


class GenericMapper:
    """Універсальний мапер для довільних об'єктів"""

    @staticmethod
    def map_list(items: List[Any], mapper_func: callable) -> List[Dict[str, Any]]:
        """Перетворення списку об'єктів"""
        return [mapper_func(item) for item in items if item]

    @staticmethod
    def map_dict_to_object(data: Dict[str, Any], target_class: Type[T]) -> T:
        """Перетворення словника в об'єкт"""
        try:
            return target_class(**data)
        except TypeError as e:
            # Фільтруємо тільки відомі поля
            import inspect
            sig = inspect.signature(target_class.__init__)
            filtered_data = {k: v for k, v in data.items()
                             if k in sig.parameters and k != 'self'}
            return target_class(**filtered_data)

    @staticmethod
    def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
        """Об'єднання декількох словників"""
        result = {}
        for d in dicts:
            if d:
                result.update(d)
        return result

    @staticmethod
    def filter_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
        """Видалення None значень зі словника"""
        return {k: v for k, v in data.items() if v is not None}


# Фабрика маперів
class MapperFactory:
    """Фабрика для створення маперів"""

    _mappers = {
        'user': UserMapper,
        'flight': FlightMapper,
        'crew_member': CrewMemberMapper,
        'crew_position': CrewPositionMapper,
        'flight_assignment': FlightAssignmentMapper,
        'operation_log': OperationLogMapper
    }

    @classmethod
    def get_mapper(cls, entity_type: str):
        """Отримання мапера за типом сутності"""
        return cls._mappers.get(entity_type.lower())

    @classmethod
    def register_mapper(cls, entity_type: str, mapper_class):
        """Реєстрація нового мапера"""
        cls._mappers[entity_type.lower()] = mapper_class