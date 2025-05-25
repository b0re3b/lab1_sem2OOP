import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from models.flight import Flight, FlightStatus
from models.flight_assignment import FlightAssignment
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class FlightRepository(BaseRepository[Flight]):
    """
    Репозиторій для роботи з рейсами
    Містить специфічні методи для управління рейсами
    """

    def __init__(self, db_session: Session):
        super().__init__(db_session, Flight)

    def get_by_flight_number(self, flight_number: str) -> Optional[Flight]:
        """Отримати рейс за номером"""
        try:
            return self.db.query(Flight).filter(
                Flight.flight_number == flight_number
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting flight by number {flight_number}: {str(e)}")
            raise

    def get_flights_by_status(self, status: FlightStatus) -> List[Flight]:
        """Отримати рейси за статусом"""
        try:
            return self.db.query(Flight).filter(
                Flight.status == status
            ).order_by(Flight.departure_time).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting flights by status {status}: {str(e)}")
            raise

    def get_flights_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Flight]:
        """Отримати рейси за період"""
        try:
            return self.db.query(Flight).filter(
                and_(
                    Flight.departure_time >= start_date,
                    Flight.departure_time <= end_date
                )
            ).order_by(Flight.departure_time).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting flights by date range: {str(e)}")
            raise

    def get_flights_by_route(self, departure_city: str, arrival_city: str) -> List[Flight]:
        """Отримати рейси за маршрутом"""
        try:
            return self.db.query(Flight).filter(
                and_(
                    Flight.departure_city == departure_city,
                    Flight.arrival_city == arrival_city
                )
            ).order_by(Flight.departure_time).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting flights by route {departure_city}-{arrival_city}: {str(e)}")
            raise

    def get_today_flights(self) -> List[Flight]:
        """Отримати рейси на сьогодні"""
        try:
            today = date.today()
            return self.db.query(Flight).filter(
                func.date(Flight.departure_time) == today
            ).order_by(Flight.departure_time).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting today's flights: {str(e)}")
            raise

    def get_upcoming_flights(self, days_ahead: int = 7) -> List[Flight]:
        """Отримати майбутні рейси на найближчі дні"""
        try:
            start_date = datetime.now()
            end_date = datetime.now().replace(hour=23, minute=59, second=59)

            from datetime import timedelta
            end_date += timedelta(days=days_ahead)

            return self.db.query(Flight).filter(
                and_(
                    Flight.departure_time >= start_date,
                    Flight.departure_time <= end_date,
                    Flight.status.in_([FlightStatus.SCHEDULED, FlightStatus.DELAYED])
                )
            ).order_by(Flight.departure_time).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting upcoming flights: {str(e)}")
            raise

    def get_flights_with_assignments(self, flight_id: Optional[int] = None) -> List[Flight]:
        """Отримати рейси з інформацією про призначення екіпажу"""
        try:
            query = self.db.query(Flight).options(
                joinedload(Flight.assignments)
            )

            if flight_id:
                query = query.filter(Flight.id == flight_id)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting flights with assignments: {str(e)}")
            raise

    def get_understaffed_flights(self) -> List[Flight]:
        """Отримати рейси з недостатнім екіпажем"""
        try:
            return self.db.query(Flight).filter(
                Flight.status.in_([FlightStatus.SCHEDULED, FlightStatus.DELAYED])
            ).filter(
                Flight.id.in_(
                    self.db.query(Flight.id)
                    .outerjoin(FlightAssignment)
                    .group_by(Flight.id)
                    .having(
                        func.count(FlightAssignment.id) < Flight.crew_required
                    )
                )
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting understaffed flights: {str(e)}")
            raise

    def get_fully_staffed_flights(self) -> List[Flight]:
        """Отримати повністю укомплектовані рейси"""
        try:
            return self.db.query(Flight).filter(
                Flight.id.in_(
                    self.db.query(Flight.id)
                    .join(FlightAssignment)
                    .group_by(Flight.id)
                    .having(
                        func.count(FlightAssignment.id) >= Flight.crew_required
                    )
                )
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting fully staffed flights: {str(e)}")
            raise

    def search_flights(self, search_params: Dict[str, Any]) -> List[Flight]:
        """Пошук рейсів за різними параметрами"""
        try:
            query = self.db.query(Flight)

            if search_params.get('flight_number'):
                query = query.filter(
                    Flight.flight_number.ilike(f"%{search_params['flight_number']}%")
                )

            if search_params.get('departure_city'):
                query = query.filter(
                    Flight.departure_city.ilike(f"%{search_params['departure_city']}%")
                )

            if search_params.get('arrival_city'):
                query = query.filter(
                    Flight.arrival_city.ilike(f"%{search_params['arrival_city']}%")
                )

            if search_params.get('aircraft_type'):
                query = query.filter(
                    Flight.aircraft_type.ilike(f"%{search_params['aircraft_type']}%")
                )

            if search_params.get('status'):
                query = query.filter(Flight.status == search_params['status'])

            if search_params.get('date_from'):
                query = query.filter(Flight.departure_time >= search_params['date_from'])

            if search_params.get('date_to'):
                query = query.filter(Flight.departure_time <= search_params['date_to'])

            return query.order_by(Flight.departure_time).all()

        except SQLAlchemyError as e:
            logger.error(f"Error searching flights: {str(e)}")
            raise

    def create_flight(self, flight_number: str, departure_city: str, arrival_city: str,
                      departure_time: datetime, arrival_time: datetime,
                      aircraft_type: str, crew_required: int = 4,
                      created_by: int = None) -> Flight:
        """Створити новий рейс"""
        try:
            # Перевірка унікальності номера рейсу
            if self.get_by_flight_number(flight_number):
                raise ValueError(f"Flight number {flight_number} already exists")

            # Валідація часу
            if departure_time >= arrival_time:
                raise ValueError("Departure time must be before arrival time")

            flight = Flight(
                flight_number=flight_number,
                departure_city=departure_city,
                arrival_city=arrival_city,
                departure_time=departure_time,
                arrival_time=arrival_time,
                aircraft_type=aircraft_type,
                crew_required=crew_required,
                status=FlightStatus.SCHEDULED,
                created_by=created_by
            )

            self.db.add(flight)
            self.db.commit()
            self.db.refresh(flight)

            logger.info(f"Created flight {flight_number}")
            return flight

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating flight {flight_number}: {str(e)}")
            raise

    def update_flight_status(self, flight_id: int, new_status: FlightStatus) -> Optional[Flight]:
        """Оновити статус рейсу"""
        try:
            flight = self.get_by_id(flight_id)
            if not flight:
                return None

            old_status = flight.status
            flight.status = new_status
            self.db.commit()
            self.db.refresh(flight)

            logger.info(f"Updated flight {flight.flight_number} status from {old_status} to {new_status}")
            return flight

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating flight status for id {flight_id}: {str(e)}")
            raise

    def get_flight_statistics(self) -> Dict[str, Any]:
        """Отримати статистику рейсів"""
        try:
            total_flights = self.db.query(Flight).count()

            status_stats = self.db.query(
                Flight.status, func.count(Flight.id)
            ).group_by(Flight.status).all()

            today_flights = len(self.get_today_flights())

            upcoming_flights = len(self.get_upcoming_flights())

            understaffed_count = len(self.get_understaffed_flights())

            return {
                'total_flights': total_flights,
                'status_distribution': dict(status_stats),
                'today_flights': today_flights,
                'upcoming_flights': upcoming_flights,
                'understaffed_flights': understaffed_count
            }

        except SQLAlchemyError as e:
            logger.error(f"Error getting flight statistics: {str(e)}")
            raise

    def get_flights_by_aircraft_type(self, aircraft_type: str) -> List[Flight]:
        """Отримати рейси за типом літака"""
        try:
            return self.db.query(Flight).filter(
                Flight.aircraft_type == aircraft_type
            ).order_by(Flight.departure_time).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting flights by aircraft type {aircraft_type}: {str(e)}")
            raise

    def cancel_flight(self, flight_id: int, reason: str = None) -> Optional[Flight]:
        """Скасувати рейс"""
        try:
            flight = self.get_by_id(flight_id)
            if not flight:
                return None

            if flight.status == FlightStatus.COMPLETED:
                raise ValueError("Cannot cancel completed flight")

            flight.status = FlightStatus.CANCELLED
            self.db.commit()
            self.db.refresh(flight)

            logger.info(f"Cancelled flight {flight.flight_number}" +
                        (f" (reason: {reason})" if reason else ""))
            return flight

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error cancelling flight with id {flight_id}: {str(e)}")
            raise