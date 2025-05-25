import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session, joinedload

from .base import BaseRepository
from ..models.flight_assignment import FlightAssignment, AssignmentStatus
from ..models.flight import Flight
from ..models.crew_member import CrewMember
from ..models.crew_position import CrewPosition

logger = logging.getLogger(__name__)


class AssignmentRepository(BaseRepository[FlightAssignment]):
    """
    Репозиторій для роботи з призначеннями екіпажу на рейси
    Реалізує специфічну логіку для управління призначеннями
    """

    def __init__(self, db_session: Session):
        super().__init__(db_session, FlightAssignment)

    def create_assignment(self, flight_id: int, crew_member_id: int,
                          assigned_by: int, notes: Optional[str] = None) -> Optional[FlightAssignment]:
        """
        Створити нове призначення з перевіркою конфліктів
        """
        try:
            # Перевіряємо чи немає конфліктуючих призначень
            if not self.check_crew_availability(crew_member_id, flight_id):
                logger.warning(f"Crew member {crew_member_id} is not available for flight {flight_id}")
                return None

            assignment = FlightAssignment(
                flight_id=flight_id,
                crew_member_id=crew_member_id,
                assigned_by=assigned_by,
                status=AssignmentStatus.ASSIGNED,
                notes=notes,
                assigned_at=datetime.utcnow()
            )

            self.db.add(assignment)
            self.db.commit()
            self.db.refresh(assignment)

            logger.info(f"Created assignment {assignment.id} for crew {crew_member_id} to flight {flight_id}")
            return assignment

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating assignment: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating assignment: {str(e)}")
            raise

    def get_assignments_by_flight(self, flight_id: int,
                                  status: Optional[AssignmentStatus] = None) -> List[FlightAssignment]:
        """
        Отримати всі призначення для конкретного рейсу
        """
        try:
            query = self.db.query(FlightAssignment).options(
                joinedload(FlightAssignment.crew_member).joinedload(CrewMember.position),
                joinedload(FlightAssignment.flight)
            ).filter(FlightAssignment.flight_id == flight_id)

            if status:
                query = query.filter(FlightAssignment.status == status)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting assignments for flight {flight_id}: {str(e)}")
            raise

    def get_assignments_by_crew_member(self, crew_member_id: int,
                                       active_only: bool = True) -> List[FlightAssignment]:
        """
        Отримати всі призначення для конкретного члена екіпажу
        """
        try:
            query = self.db.query(FlightAssignment).options(
                joinedload(FlightAssignment.flight),
                joinedload(FlightAssignment.crew_member)
            ).filter(FlightAssignment.crew_member_id == crew_member_id)

            if active_only:
                query = query.filter(FlightAssignment.status == AssignmentStatus.ASSIGNED)

            return query.order_by(FlightAssignment.assigned_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting assignments for crew member {crew_member_id}: {str(e)}")
            raise

    def check_crew_availability(self, crew_member_id: int, flight_id: int) -> bool:
        """
        Перевірити доступність члена екіпажу для призначення на рейс
        """
        try:
            # Отримуємо інформацію про рейс
            flight = self.db.query(Flight).filter(Flight.id == flight_id).first()
            if not flight:
                return False

            # Використовуємо функцію PostgreSQL для перевірки доступності
            result = self.db.execute(
                text("SELECT check_crew_availability(:crew_id, :departure, :arrival)"),
                {
                    'crew_id': crew_member_id,
                    'departure': flight.departure_time,
                    'arrival': flight.arrival_time
                }
            ).scalar()

            return bool(result)
        except SQLAlchemyError as e:
            logger.error(f"Error checking crew availability: {str(e)}")
            return False

    def get_conflicting_assignments(self, crew_member_id: int,
                                    departure_time: datetime,
                                    arrival_time: datetime) -> List[FlightAssignment]:
        """
        Знайти конфліктуючі призначення для члена екіпажу
        """
        try:
            return self.db.query(FlightAssignment).join(Flight).filter(
                and_(
                    FlightAssignment.crew_member_id == crew_member_id,
                    FlightAssignment.status == AssignmentStatus.ASSIGNED,
                    or_(
                        and_(Flight.departure_time <= departure_time, Flight.arrival_time >= departure_time),
                        and_(Flight.departure_time <= arrival_time, Flight.arrival_time >= arrival_time),
                        and_(Flight.departure_time >= departure_time, Flight.arrival_time <= arrival_time)
                    )
                )
            ).options(joinedload(FlightAssignment.flight)).all()
        except SQLAlchemyError as e:
            logger.error(f"Error finding conflicting assignments: {str(e)}")
            raise

    def confirm_assignment(self, assignment_id: int) -> Optional[FlightAssignment]:
        """
        Підтвердити призначення
        """
        try:
            assignment = self.get_by_id(assignment_id)
            if not assignment:
                return None

            assignment.confirm()
            self.db.commit()
            self.db.refresh(assignment)

            logger.info(f"Confirmed assignment {assignment_id}")
            return assignment
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error confirming assignment {assignment_id}: {str(e)}")
            raise

    def cancel_assignment(self, assignment_id: int, reason: Optional[str] = None) -> Optional[FlightAssignment]:
        """
        Скасувати призначення
        """
        try:
            assignment = self.get_by_id(assignment_id)
            if not assignment:
                return None

            assignment.cancel()
            if reason:
                assignment.notes = f"{assignment.notes or ''}\nCancelled: {reason}"

            self.db.commit()
            self.db.refresh(assignment)

            logger.info(f"Cancelled assignment {assignment_id}")
            return assignment
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error cancelling assignment {assignment_id}: {str(e)}")
            raise

    def get_flight_crew_statistics(self, flight_id: int) -> Dict[str, Any]:
        """
        Отримати статистику по екіпажу рейсу
        """
        try:
            # Використовуємо представлення flight_statistics
            result = self.db.execute(
                text("SELECT * FROM flight_statistics WHERE flight_id = :flight_id"),
                {'flight_id': flight_id}
            ).fetchone()

            if result:
                return {
                    'flight_id': result.flight_id,
                    'flight_number': result.flight_number,
                    'departure_city': result.departure_city,
                    'arrival_city': result.arrival_city,
                    'status': result.status,
                    'assigned_crew_count': result.assigned_crew_count,
                    'crew_required': result.crew_required,
                    'staffing_status': result.staffing_status
                }
            return {}
        except SQLAlchemyError as e:
            logger.error(f"Error getting flight crew statistics for flight {flight_id}: {str(e)}")
            raise

    def get_assignments_by_date_range(self, start_date: datetime,
                                      end_date: datetime,
                                      status: Optional[AssignmentStatus] = None) -> List[FlightAssignment]:
        """
        Отримати призначення в заданому діапазоні дат
        """
        try:
            query = self.db.query(FlightAssignment).join(Flight).options(
                joinedload(FlightAssignment.flight),
                joinedload(FlightAssignment.crew_member).joinedload(CrewMember.position)
            ).filter(
                and_(
                    Flight.departure_time >= start_date,
                    Flight.departure_time <= end_date
                )
            )

            if status:
                query = query.filter(FlightAssignment.status == status)

            return query.order_by(Flight.departure_time).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting assignments by date range: {str(e)}")
            raise

    def bulk_assign_crew(self, assignments_data: List[Dict[str, Any]]) -> List[FlightAssignment]:
        """
        Масове призначення екіпажу
        """
        try:
            created_assignments = []

            for data in assignments_data:
                assignment = self.create_assignment(
                    flight_id=data['flight_id'],
                    crew_member_id=data['crew_member_id'],
                    assigned_by=data['assigned_by'],
                    notes=data.get('notes')
                )
                if assignment:
                    created_assignments.append(assignment)

            logger.info(f"Bulk assigned {len(created_assignments)} crew members")
            return created_assignments
        except SQLAlchemyError as e:
            logger.error(f"Error in bulk crew assignment: {str(e)}")
            raise

    def get_crew_workload(self, crew_member_id: int,
                          start_date: datetime,
                          end_date: datetime) -> Dict[str, Any]:
        """
        Отримати навантаження члена екіпажу за період
        """
        try:
            assignments = self.db.query(FlightAssignment).join(Flight).filter(
                and_(
                    FlightAssignment.crew_member_id == crew_member_id,
                    FlightAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.CONFIRMED]),
                    Flight.departure_time >= start_date,
                    Flight.departure_time <= end_date
                )
            ).options(joinedload(FlightAssignment.flight)).all()

            total_flights = len(assignments)
            total_hours = sum(
                (assignment.flight.arrival_time - assignment.flight.departure_time).total_seconds() / 3600
                for assignment in assignments
            )

            return {
                'crew_member_id': crew_member_id,
                'period_start': start_date,
                'period_end': end_date,
                'total_flights': total_flights,
                'total_flight_hours': round(total_hours, 2),
                'assignments': assignments
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting crew workload: {str(e)}")
            raise