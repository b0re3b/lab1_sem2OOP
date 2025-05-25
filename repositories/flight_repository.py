from typing import List, Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from config.database import DatabaseConfig
from config.logging_config import log_database_operation
from models.flight import Flight
from utils.validators import FlightValidator


class FlightRepository:
    def __init__(self):
        self.table_name = "flights"
        self.validator = FlightValidator()
        self.db_manager = DatabaseConfig()
    @log_database_operation
    def create_flight(self, flight_data: Dict[str, Any]) -> Optional[Flight]:
        """Створення нового рейсу"""
        self.validator.validate_flight_data(flight_data)

        query = """
                INSERT INTO flights (flight_number, departure_city, arrival_city, departure_time,
                                     arrival_time, aircraft_type, status, crew_required, created_by)
                VALUES (%(flight_number)s, %(departure_city)s, %(arrival_city)s, %(departure_time)s,
                        %(arrival_time)s, %(aircraft_type)s, %(status)s, %(crew_required)s, %(created_by)s)
                RETURNING * \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, flight_data)
                    result = cursor.fetchone()
                    conn.commit()
                    return Flight(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error creating flight: {e}")

    @log_database_operation
    def find_by_id(self, flight_id: int) -> Optional[Flight]:
        """Пошук рейсу за ID"""
        query = "SELECT * FROM flights WHERE id = %s"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (flight_id,))
                    result = cursor.fetchone()
                    return Flight(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error finding flight by id: {e}")

    @log_database_operation
    def find_by_flight_number(self, flight_number: str) -> Optional[Flight]:
        """Пошук рейсу за номером"""
        self.validator.validate_flight_number(flight_number)

        query = "SELECT * FROM flights WHERE flight_number = %s"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (flight_number,))
                    result = cursor.fetchone()
                    return Flight(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error finding flight by number: {e}")

    @log_database_operation
    def find_all_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Flight]:
        """Пошук рейсів за періодом"""
        query = """
                SELECT * \
                FROM flights
                WHERE departure_time >= %s \
                  AND departure_time <= %s
                ORDER BY departure_time \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (start_date, end_date))
                    results = cursor.fetchall()
                    return [Flight(**dict(row)) for row in results]
        except psycopg2.Error as e:
            raise Exception(f"Database error finding flights by date range: {e}")

    @log_database_operation
    def find_all_by_status(self, status: str) -> List[Flight]:
        """Пошук рейсів за статусом"""
        query = "SELECT * FROM flights WHERE status = %s ORDER BY departure_time"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (status,))
                    results = cursor.fetchall()
                    return [Flight(**dict(row)) for row in results]
        except psycopg2.Error as e:
            raise Exception(f"Database error finding flights by status: {e}")

    @log_database_operation
    def find_flights_needing_crew(self) -> List[Flight]:
        """Пошук рейсів, які потребують екіпаж"""
        query = """
                SELECT f.* \
                FROM flights f \
                         LEFT JOIN (SELECT flight_id, COUNT(*) as assigned_count \
                                    FROM flight_assignments \
                                    WHERE status = 'ASSIGNED' \
                                    GROUP BY flight_id) fa ON f.id = fa.flight_id
                WHERE COALESCE(fa.assigned_count, 0) < f.crew_required
                  AND f.status = 'SCHEDULED'
                ORDER BY f.departure_time \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query)
                    results = cursor.fetchall()
                    return [Flight(**dict(row)) for row in results]
        except psycopg2.Error as e:
            raise Exception(f"Database error finding flights needing crew: {e}")

    @log_database_operation
    def update_flight(self, flight_id: int, update_data: Dict[str, Any]) -> Optional[Flight]:
        """Оновлення рейсу"""
        if not update_data:
            return self.find_by_id(flight_id)

        set_clause = ", ".join([f"{key} = %({key})s" for key in update_data.keys()])
        query = f"UPDATE flights SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %(id)s RETURNING *"

        update_data['id'] = flight_id

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, update_data)
                    result = cursor.fetchone()
                    conn.commit()
                    return Flight(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error updating flight: {e}")

    @log_database_operation
    def update_flight_status(self, flight_id: int, status: str) -> bool:
        """Оновлення статусу рейсу"""
        query = "UPDATE flights SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (status, flight_id))
                    conn.commit()
                    return cursor.rowcount > 0
        except psycopg2.Error as e:
            raise Exception(f"Database error updating flight status: {e}")

    @log_database_operation
    def delete_flight(self, flight_id: int) -> bool:
        """Видалення рейсу"""
        query = "DELETE FROM flights WHERE id = %s"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (flight_id,))
                    conn.commit()
                    return cursor.rowcount > 0
        except psycopg2.Error as e:
            raise Exception(f"Database error deleting flight: {e}")