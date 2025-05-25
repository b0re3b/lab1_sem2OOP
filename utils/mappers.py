from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class UserDTO:
    """DTO для користувача"""
    id: Optional[int] = None
    keycloak_id: Optional[str] = None
    username: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    role: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class FlightDTO:
    """DTO для рейсу"""
    id: Optional[int] = None
    flight_number: str = ""
    departure_city: str = ""
    arrival_city: str = ""
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    aircraft_type: str = ""
    status: str = "SCHEDULED"
    crew_required: int = 4
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class CrewMemberDTO:
    """DTO для члена екіпажу"""
    id: Optional[int] = None
    employee_id: str = ""
    first_name: str = ""
    last_name: str = ""
    position_id: int = 0
    position_name: Optional[str] = None
    experience_years: int = 0
    certification_level: str = "JUNIOR"
    is_available: bool = True
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class FlightAssignmentDTO:
    """DTO для призначення екіпажу на рейс"""
    id: Optional[int] = None
    flight_id: int = 0
    crew_member_id: int = 0
    assigned_by: int = 0
    assigned_at: Optional[datetime] = None
    status: str = "ASSIGNED"
    notes: Optional[str] = None
    # Додаткові поля для зручності
    flight_number: Optional[str] = None
    crew_member_name: Optional[str] = None
    position_name: Optional[str] = None
    assigned_by_name: Optional[str] = None


class BaseMapper(ABC):
    """Базовий клас для всіх мапперів"""

    @abstractmethod
    def to_dto(self, entity: Any) -> Any:
        """Конвертація з entity в DTO"""
        pass

    @abstractmethod
    def to_entity(self, dto: Any) -> Any:
        """Конвертація з DTO в entity"""
        pass

    @abstractmethod
    def to_dict(self, dto: Any) -> Dict[str, Any]:
        """Конвертація DTO в словник"""
        pass

    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> Any:
        """Створення DTO зі словника"""
        pass


class UserMapper(BaseMapper):
    """Маппер для користувачів"""

    def to_dto(self, entity: Any) -> UserDTO | None:
        """Конвертація з SQLAlchemy entity в UserDTO"""
        if not entity:
            return None

        return UserDTO(
            id=entity.id,
            keycloak_id=entity.keycloak_id,
            username=entity.username,
            email=entity.email,
            first_name=entity.first_name,
            last_name=entity.last_name,
            role=entity.role,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    def to_entity(self, dto: UserDTO) -> Dict[str, Any]:
        """Конвертація UserDTO в дані для entity"""
        return {
            'keycloak_id': dto.keycloak_id,
            'username': dto.username,
            'email': dto.email,
            'first_name': dto.first_name,
            'last_name': dto.last_name,
            'role': dto.role,
            'is_active': dto.is_active
        }

    def to_dict(self, dto: UserDTO) -> Dict[str, Any]:
        """Конвертація UserDTO в словник"""
        return {
            'id': dto.id,
            'keycloak_id': dto.keycloak_id,
            'username': dto.username,
            'email': dto.email,
            'first_name': dto.first_name,
            'last_name': dto.last_name,
            'role': dto.role,
            'is_active': dto.is_active,
            'created_at': dto.created_at.isoformat() if dto.created_at else None,
            'updated_at': dto.updated_at.isoformat() if dto.updated_at else None
        }

    def from_dict(self, data: Dict[str, Any]) -> UserDTO:
        """Створення UserDTO зі словника"""
        return UserDTO(
            id=data.get('id'),
            keycloak_id=data.get('keycloak_id'),
            username=data.get('username', ''),
            email=data.get('email', ''),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role=data.get('role', ''),
            is_active=data.get('is_active', True),
            created_at=self._parse_datetime(data.get('created_at')),
            updated_at=self._parse_datetime(data.get('updated_at'))
        )

    def to_list_dto(self, entities: List[Any]) -> List[UserDTO]:
        """Конвертація списку entities в список DTO"""
        return [self.to_dto(entity) for entity in entities if entity]

    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Парсинг datetime з рядка"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None


class FlightMapper(BaseMapper):
    """Маппер для рейсів"""

    def to_dto(self, entity: Any) -> FlightDTO | None:
        """Конвертація з SQLAlchemy entity в FlightDTO"""
        if not entity:
            return None

        return FlightDTO(
            id=entity.id,
            flight_number=entity.flight_number,
            departure_city=entity.departure_city,
            arrival_city=entity.arrival_city,
            departure_time=entity.departure_time,
            arrival_time=entity.arrival_time,
            aircraft_type=entity.aircraft_type,
            status=entity.status,
            crew_required=entity.crew_required,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    def to_entity(self, dto: FlightDTO) -> Dict[str, Any]:
        """Конвертація FlightDTO в дані для entity"""
        return {
            'flight_number': dto.flight_number,
            'departure_city': dto.departure_city,
            'arrival_city': dto.arrival_city,
            'departure_time': dto.departure_time,
            'arrival_time': dto.arrival_time,
            'aircraft_type': dto.aircraft_type,
            'status': dto.status,
            'crew_required': dto.crew_required,
            'created_by': dto.created_by
        }

    def to_dict(self, dto: FlightDTO) -> Dict[str, Any]:
        """Конвертація FlightDTO в словник"""
        return {
            'id': dto.id,
            'flight_number': dto.flight_number,
            'departure_city': dto.departure_city,
            'arrival_city': dto.arrival_city,
            'departure_time': dto.departure_time.isoformat() if dto.departure_time else None,
            'arrival_time': dto.arrival_time.isoformat() if dto.arrival_time else None,
            'aircraft_type': dto.aircraft_type,
            'status': dto.status,
            'crew_required': dto.crew_required,
            'created_by': dto.created_by,
            'created_at': dto.created_at.isoformat() if dto.created_at else None,
            'updated_at': dto.updated_at.isoformat() if dto.updated_at else None
        }

    def from_dict(self, data: Dict[str, Any]) -> FlightDTO:
        """Створення FlightDTO зі словника"""
        return FlightDTO(
            id=data.get('id'),
            flight_number=data.get('flight_number', ''),
            departure_city=data.get('departure_city', ''),
            arrival_city=data.get('arrival_city', ''),
            departure_time=self._parse_datetime(data.get('departure_time')),
            arrival_time=self._parse_datetime(data.get('arrival_time')),
            aircraft_type=data.get('aircraft_type', ''),
            status=data.get('status', 'SCHEDULED'),
            crew_required=data.get('crew_required', 4),
            created_by=data.get('created_by'),
            created_at=self._parse_datetime(data.get('created_at')),
            updated_at=self._parse_datetime(data.get('updated_at'))
        )

    def to_list_dto(self, entities: List[Any]) -> List[FlightDTO]:
        """Конвертація списку entities в список DTO"""
        return [self.to_dto(entity) for entity in entities if entity]

    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Парсинг datetime з рядка"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None


class CrewMemberMapper(BaseMapper):
    """Маппер для членів екіпажу"""

    def to_dto(self, entity: Any) -> CrewMemberDTO | None:
        """Конвертація з SQLAlchemy entity в CrewMemberDTO"""
        if not entity:
            return None

        return CrewMemberDTO(
            id=entity.id,
            employee_id=entity.employee_id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            position_id=entity.position_id,
            position_name=getattr(entity, 'position_name', None),
            experience_years=entity.experience_years,
            certification_level=entity.certification_level,
            is_available=entity.is_available,
            phone=entity.phone,
            email=entity.email,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    def to_entity(self, dto: CrewMemberDTO) -> Dict[str, Any]:
        """Конвертація CrewMemberDTO в дані для entity"""
        return {
            'employee_id': dto.employee_id,
            'first_name': dto.first_name,
            'last_name': dto.last_name,
            'position_id': dto.position_id,
            'experience_years': dto.experience_years,
            'certification_level': dto.certification_level,
            'is_available': dto.is_available,
            'phone': dto.phone,
            'email': dto.email
        }

    def to_dict(self, dto: CrewMemberDTO) -> Dict[str, Any]:
        """Конвертація CrewMemberDTO в словник"""
        return {
            'id': dto.id,
            'employee_id': dto.employee_id,
            'first_name': dto.first_name,
            'last_name': dto.last_name,
            'position_id': dto.position_id,
            'position_name': dto.position_name,
            'experience_years': dto.experience_years,
            'certification_level': dto.certification_level,
            'is_available': dto.is_available,
            'phone': dto.phone,
            'email': dto.email,
            'created_at': dto.created_at.isoformat() if dto.created_at else None,
            'updated_at': dto.updated_at.isoformat() if dto.updated_at else None
        }

    def from_dict(self, data: Dict[str, Any]) -> CrewMemberDTO:
        """Створення CrewMemberDTO зі словника"""
        return CrewMemberDTO(
            id=data.get('id'),
            employee_id=data.get('employee_id', ''),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            position_id=data.get('position_id', 0),
            position_name=data.get('position_name'),
            experience_years=data.get('experience_years', 0),
            certification_level=data.get('certification_level', 'JUNIOR'),
            is_available=data.get('is_available', True),
            phone=data.get('phone'),
            email=data.get('email'),
            created_at=self._parse_datetime(data.get('created_at')),
            updated_at=self._parse_datetime(data.get('updated_at'))
        )

    def to_list_dto(self, entities: List[Any]) -> List[CrewMemberDTO]:
        """Конвертація списку entities в список DTO"""
        return [self.to_dto(entity) for entity in entities if entity]

    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Парсинг datetime з рядка"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None


class FlightAssignmentMapper(BaseMapper):
    """Маппер для призначень екіпажу на рейси"""

    def to_dto(self, entity: Any) -> FlightAssignmentDTO | None:
        """Конвертація з SQLAlchemy entity в FlightAssignmentDTO"""
        if not entity:
            return None

        return FlightAssignmentDTO(
            id=entity.id,
            flight_id=entity.flight_id,
            crew_member_id=entity.crew_member_id,
            assigned_by=entity.assigned_by,
            assigned_at=entity.assigned_at,
            status=entity.status,
            notes=entity.notes,
            flight_number=getattr(entity, 'flight_number', None),
            crew_member_name=getattr(entity, 'crew_member_name', None),
            position_name=getattr(entity, 'position_name', None),
            assigned_by_name=getattr(entity, 'assigned_by_name', None)
        )

    def to_entity(self, dto: FlightAssignmentDTO) -> Dict[str, Any]:
        """Конвертація FlightAssignmentDTO в дані для entity"""
        return {
            'flight_id': dto.flight_id,
            'crew_member_id': dto.crew_member_id,
            'assigned_by': dto.assigned_by,
            'status': dto.status,
            'notes': dto.notes
        }

    def to_dict(self, dto: FlightAssignmentDTO) -> Dict[str, Any]:
        """Конвертація FlightAssignmentDTO в словник"""
        return {
            'id': dto.id,
            'flight_id': dto.flight_id,
            'crew_member_id': dto.crew_member_id,
            'assigned_by': dto.assigned_by,
            'assigned_at': dto.assigned_at.isoformat() if dto.assigned_at else None,
            'status': dto.status,
            'notes': dto.notes,
            'flight_number': dto.flight_number,
            'crew_member_name': dto.crew_member_name,
            'position_name': dto.position_name,
            'assigned_by_name': dto.assigned_by_name
        }

    def from_dict(self, data: Dict[str, Any]) -> FlightAssignmentDTO:
        """Створення FlightAssignmentDTO зі словника"""
        return FlightAssignmentDTO(
            id=data.get('id'),
            flight_id=data.get('flight_id', 0),
            crew_member_id=data.get('crew_member_id', 0),
            assigned_by=data.get('assigned_by', 0),
            assigned_at=self._parse_datetime(data.get('assigned_at')),
            status=data.get('status', 'ASSIGNED'),
            notes=data.get('notes'),
            flight_number=data.get('flight_number'),
            crew_member_name=data.get('crew_member_name'),
            position_name=data.get('position_name'),
            assigned_by_name=data.get('assigned_by_name')
        )

    def to_list_dto(self, entities: List[Any]) -> List[FlightAssignmentDTO]:
        """Конвертація списку entities в список DTO"""
        return [self.to_dto(entity) for entity in entities if entity]

    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Парсинг datetime з рядка"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None