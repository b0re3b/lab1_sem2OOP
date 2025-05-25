import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import and_, or_, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session, joinedload

from .base import BaseRepository
from ..models.crew_member import CrewMember, CertificationLevel
from ..models.crew_position import CrewPosition
from ..models.flight import Flight
from ..models.flight_assignment import FlightAssignment, AssignmentStatus

logger = logging.getLogger(__name__)


class CrewRepository(BaseRepository[CrewMember]):
    """
    Репозиторій для роботи з членами екіпажу
    Реалізує специфічну логіку для управління екіпажем
    """

    def __init__(self, db_session: Session):
        super().__init__(db_session, CrewMember)

    def create_crew_member(self, employee_id: str, first_name: str, last_name: str,
                           position_id: int, experience_years: int = 0,
                           certification_level: CertificationLevel = CertificationLevel.JUNIOR,
                           phone: Optional[str] = None, email: Optional[str] = None) -> Optional[CrewMember]:
        """
        Створити нового члена екіпажу
        """
        try:
            crew_member = CrewMember(
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                position_id=position_id,
                experience_years=experience_years,
                certification_level=certification_level,
                phone=phone,
                email=email,
                is_available=True
            )

            self.db.add(crew_member)
            self.db.commit()
            self.db.refresh(crew_member)

            logger.info(f"Created crew member {crew_member.employee_id}: {crew_member.full_name}")
            return crew_member

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating crew member: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating crew member: {str(e)}")
            raise

    def get_by_employee_id(self, employee_id: str) -> Optional[CrewMember]:
        """
        Отримати члена екіпажу за службовим номером
        """
        try:
            return self.db.query(CrewMember).options(
                joinedload(CrewMember.position)
            ).filter(CrewMember.employee_id == employee_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting crew member by employee_id {employee_id}: {str(e)}")
            raise

    def get_by_position(self, position_id: int, available_only: bool = True) -> List[CrewMember]:
        """
        Отримати всіх членів екіпажу за посадою
        """
        try:
            query = self.db.query(CrewMember).options(
                joinedload(CrewMember.position)
            ).filter(CrewMember.position_id == position_id)

            if available_only:
                query = query.filter(CrewMember.is_available == True)

            return query.order_by(CrewMember.experience_years.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting crew members by position {position_id}: {str(e)}")
            raise

    def get_available_crew(self, departure_time: datetime, arrival_time: datetime,
                           position_id: Optional[int] = None) -> List[CrewMember]:
        """
        Отримати доступних членів екіпажу на конкретний час
        """
        try:
            # Підзапит для знаходження зайнятих членів екіпажу
            busy_crew_subquery = self.db.query(FlightAssignment.crew_member_id).join(Flight).filter(
                and_(
                    FlightAssignment.status == AssignmentStatus.ASSIGNED,
                    or_(
                        and_(Flight.departure_time <= departure_time, Flight.arrival_time >= departure_time),
                        and_(Flight.departure_time <= arrival_time, Flight.arrival_time >= arrival_time),
                        and_(Flight.departure_time >= departure_time, Flight.arrival_time <= arrival_time)
                    )
                )
            ).subquery()

            query = self.db.query(CrewMember).options(
                joinedload(CrewMember.position)
            ).filter(
                and_(
                    CrewMember.is_available == True,
                    ~CrewMember.id.in_(busy_crew_subquery)
                )
            )

            if position_id:
                query = query.filter(CrewMember.position_id == position_id)

            return query.order_by(CrewMember.certification_level.desc(),
                                  CrewMember.experience_years.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting available crew: {str(e)}")
            raise

    def get_crew_by_certification(self, certification_level: CertificationLevel,
                                  position_id: Optional[int] = None) -> List[CrewMember]:
        """
        Отримати членів екіпажу за рівнем сертифікації
        """
        try:
            query = self.db.query(CrewMember).options(
                joinedload(CrewMember.position)
            ).filter(CrewMember.certification_level == certification_level)

            if position_id:
                query = query.filter(CrewMember.position_id == position_id)

            return query.order_by(CrewMember.experience_years.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting crew by certification: {str(e)}")
            raise

    def get_captains(self) -> List[CrewMember]:
        """
        Отримати всіх капітанів (пілотів з рівнем CAPTAIN)
        """
        try:
            pilot_position = self.db.query(CrewPosition).filter(
                CrewPosition.position_name == 'PILOT'
            ).first()

            if not pilot_position:
                return []

            return self.db.query(CrewMember).options(
                joinedload(CrewMember.position)
            ).filter(
                and_(
                    CrewMember.position_id == pilot_position.id,
                    CrewMember.certification_level == CertificationLevel.CAPTAIN
                )
            ).order_by(CrewMember.experience_years.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting captains: {str(e)}")
            raise

    def get_senior_crew(self, position_name: Optional[str] = None) -> List[CrewMember]:
        """
        Отримати досвідчених членів екіпажу (SENIOR та CAPTAIN)
        """
        try:
            query = self.db.query(CrewMember).options(
                joinedload(CrewMember.position)
            ).filter(
                CrewMember.certification_level.in_([CertificationLevel.SENIOR, CertificationLevel.CAPTAIN])
            )

            if position_name:
                query = query.join(CrewPosition).filter(CrewPosition.position_name == position_name)

            return query.order_by(CrewMember.certification_level.desc(),
                                  CrewMember.experience_years.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting senior crew: {str(e)}")
            raise

    def set_availability(self, crew_member_id: int, is_available: bool) -> Optional[CrewMember]:
        """
        Встановити доступність члена екіпажу
        """
        try:
            crew_member = self.get_by_id(crew_member_id)
            if not crew_member:
                return None

            crew_member.is_available = is_available
            self.db.commit()
            self.db.refresh(crew_member)

            logger.info(f"Set availability for {crew_member.employee_id} to {is_available}")
            return crew_member
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error setting availability for crew member {crew_member_id}: {str(e)}")
            raise

    def promote_crew_member(self, crew_member_id: int) -> Optional[CrewMember]:
        """
        Підвищити рівень сертифікації члена екіпажу
        """
        try:
            crew_member = self.get_by_id(crew_member_id)
            if not crew_member:
                return None

            current_level = crew_member.certification_level
            if current_level == CertificationLevel.JUNIOR:
                crew_member.certification_level = CertificationLevel.SENIOR
            elif current_level == CertificationLevel.SENIOR:
                crew_member.certification_level = CertificationLevel.CAPTAIN

            self.db.commit()
            self.db.refresh(crew_member)

            logger.info(
                f"Promoted {crew_member.employee_id} from {current_level.value} to {crew_member.certification_level.value}")
            return crew_member
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error promoting crew member {crew_member_id}: {str(e)}")
            raise

    def get_crew_statistics(self) -> Dict[str, Any]:
        """
        Отримати статистику по екіпажу
        """
        try:
            total_crew = self.db.query(func.count(CrewMember.id)).scalar()
            available_crew = self.db.query(func.count(CrewMember.id)).filter(
                CrewMember.is_available == True
            ).scalar()

            # Статистика за посадами
            position_stats = self.db.query(
                CrewPosition.position_name,
                func.count(CrewMember.id).label('count')
            ).join(CrewMember).group_by(CrewPosition.position_name).all()

            # Статистика за рівнями сертифікації
            certification_stats = self.db.query(
                CrewMember.certification_level,
                func.count(CrewMember.id).label('count')
            ).group_by(CrewMember.certification_level).all()

            return {
                'total_crew_members': total_crew,
                'available_crew_members': available_crew,
                'unavailable_crew_members': total_crew - available_crew,
                'positions': [{'position': pos.position_name, 'count': pos.count} for pos in position_stats],
                'certifications': [{'level': cert.certification_level.value, 'count': cert.count} for cert in
                                   certification_stats]
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting crew statistics: {str(e)}")
            raise

    def get_crew_workload_report(self, start_date: datetime,
                                 end_date: datetime) -> List[Dict[str, Any]]:
        """
        Отримати звіт про навантаження екіпажу за період
        """
        try:
            # Запит для підрахунку навантаження кожного члена екіпажу
            workload_query = self.db.query(
                CrewMember.id,
                CrewMember.employee_id,
                CrewMember.first_name,
                CrewMember.last_name,
                CrewPosition.position_name,
                func.count(FlightAssignment.id).label('flight_count'),
                func.sum(
                    func.extract('epoch', Flight.arrival_time - Flight.departure_time) / 3600
                ).label('total_hours')
            ).join(CrewPosition).outerjoin(FlightAssignment).outerjoin(Flight).filter(
                and_(
                    Flight.departure_time >= start_date,
                    Flight.departure_time <= end_date,
                    FlightAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.CONFIRMED])
                )
            ).group_by(
                CrewMember.id, CrewMember.employee_id, CrewMember.first_name,
                CrewMember.last_name, CrewPosition.position_name
            ).all()

            return [
                {
                    'crew_member_id': row.id,
                    'employee_id': row.employee_id,
                    'full_name': f"{row.first_name} {row.last_name}",
                    'position': row.position_name,
                    'flight_count': row.flight_count or 0,
                    'total_hours': round(float(row.total_hours or 0), 2)
                }
                for row in workload_query
            ]
        except SQLAlchemyError as e:
            logger.error(f"Error getting crew workload report: {str(e)}")
            raise

    def search_crew_members(self, search_term: str, position_id: Optional[int] = None,
                            available_only: bool = False) -> List[CrewMember]:
        """
        Пошук членів екіпажу за іменем або службовим номером
        """
        try:
            search_pattern = f"%{search_term}%"
            query = self.db.query(CrewMember).options(
                joinedload(CrewMember.position)
            ).filter(
                or_(
                    CrewMember.first_name.ilike(search_pattern),
                    CrewMember.last_name.ilike(search_pattern),
                    CrewMember.employee_id.ilike(search_pattern),
                    (CrewMember.first_name + ' ' + CrewMember.last_name).ilike(search_pattern)
                )
            )

            if position_id:
                query = query.filter(CrewMember.position_id == position_id)

            if available_only:
                query = query.filter(CrewMember.is_available == True)

            return query.order_by(CrewMember.last_name, CrewMember.first_name).all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching crew members: {str(e)}")
            raise

    def get_crew_with_assignments(self, crew_member_id: int) -> Optional[Dict[str, Any]]:
        """
        Отримати члена екіпажу з усіма його поточними призначеннями
        """
        try:
            crew_member = self.db.query(CrewMember).options(
                joinedload(CrewMember.position)
            ).filter(CrewMember.id == crew_member_id).first()

            if not crew_member:
                return None

            # Отримуємо активні призначення
            active_assignments = self.db.query(FlightAssignment).options(
                joinedload(FlightAssignment.flight)
            ).filter(
                and_(
                    FlightAssignment.crew_member_id == crew_member_id,
                    FlightAssignment.status == AssignmentStatus.ASSIGNED,
                    Flight.departure_time >= datetime.utcnow()
                )
            ).join(Flight).order_by(Flight.departure_time).all()

            return {
                'crew_member': crew_member,
                'active_assignments': active_assignments,
                'assignment_count': len(active_assignments)
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting crew member with assignments: {str(e)}")
            raise