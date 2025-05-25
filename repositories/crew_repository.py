from typing import List, Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from config.database import DatabaseConfig
from config.logging_config import log_database_operation
from models.crew_member import CrewMember
from models.crew_position import CrewPosition
from utils.validators import CrewValidator


class CrewRepository:
    def __init__(self):
        self.table_name = "crew_members"
        self.validator = CrewValidator()
        self.db_manager = DatabaseConfig()

    @log_database_operation
    def create_crew_member(self, crew_data: Dict[str, Any]) -> Optional[CrewMember]:
        """Створення нового члена екіпажу"""
        self.validator.validate_crew_member_data(crew_data)

        query = """
                INSERT INTO crew_members (employee_id, first_name, last_name, position_id,
                                          experience_years, certification_level, is_available, phone, email)
                VALUES (%(employee_id)s, %(first_name)s, %(last_name)s, %(position_id)s,
                        %(experience_years)s, %(certification_level)s, %(is_available)s, %(phone)s, %(email)s)
                RETURNING * \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, crew_data)
                    result = cursor.fetchone()
                    conn.commit()
                    return CrewMember(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error creating crew member: {e}")

    @log_database_operation
    def find_by_id(self, crew_id: int) -> Optional[CrewMember]:
        """Пошук члена екіпажу за ID"""
        query = """
                SELECT cm.*, cp.position_name, cp.description as position_description
                FROM crew_members cm
                         JOIN crew_positions cp ON cm.position_id = cp.id
                WHERE cm.id = %s \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (crew_id,))
                    result = cursor.fetchone()
                    return CrewMember(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error finding crew member by id: {e}")

    @log_database_operation
    def find_by_employee_id(self, employee_id: str) -> Optional[CrewMember]:
        """Пошук члена екіпажу за службовим номером"""
        self.validator.validate_employee_id(employee_id)

        query = """
                SELECT cm.*, cp.position_name, cp.description as position_description
                FROM crew_members cm
                         JOIN crew_positions cp ON cm.position_id = cp.id
                WHERE cm.employee_id = %s \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (employee_id,))
                    result = cursor.fetchone()
                    return CrewMember(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error finding crew member by employee_id: {e}")

    @log_database_operation
    def find_available_by_position(self, position_id: int) -> List[CrewMember]:
        """Пошук доступних членів екіпажу за посадою"""
        query = """
                SELECT cm.*, cp.position_name, cp.description as position_description
                FROM crew_members cm
                         JOIN crew_positions cp ON cm.position_id = cp.id
                WHERE cm.position_id = %s \
                  AND cm.is_available = TRUE
                ORDER BY cm.certification_level DESC, cm.experience_years DESC \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (position_id,))
                    results = cursor.fetchall()
                    return [CrewMember(**dict(row)) for row in results]
        except psycopg2.Error as e:
            raise Exception(f"Database error finding available crew by position: {e}")

    @log_database_operation
    def find_available_for_flight(self, departure_time: datetime, arrival_time: datetime) -> List[CrewMember]:
        """Пошук доступних членів екіпажу для рейсу"""
        query = """
                SELECT DISTINCT cm.*, cp.position_name, cp.description as position_description
                FROM crew_members cm
                         JOIN crew_positions cp ON cm.position_id = cp.id
                WHERE cm.is_available = TRUE
                  AND cm.id NOT IN (SELECT fa.crew_member_id \
                                    FROM flight_assignments fa \
                                             JOIN flights f ON fa.flight_id = f.id \
                                    WHERE fa.status = 'ASSIGNED' \
                                      AND ( \
                                        (f.departure_time <= %s AND f.arrival_time >= %s) \
                                            OR (f.departure_time <= %s AND f.arrival_time >= %s) \
                                            OR (f.departure_time >= %s AND f.arrival_time <= %s) \
                                        ))
                ORDER BY cp.position_name, cm.certification_level DESC, cm.experience_years DESC \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (departure_time, departure_time, arrival_time, arrival_time,
                                           departure_time, arrival_time))
                    results = cursor.fetchall()
                    return [CrewMember(**dict(row)) for row in results]
        except psycopg2.Error as e:
            raise Exception(f"Database error finding available crew for flight: {e}")

    @log_database_operation
    def update_crew_member(self, crew_id: int, update_data: Dict[str, Any]) -> Optional[CrewMember]:
        """Оновлення даних члена екіпажу"""
        if not update_data:
            return self.find_by_id(crew_id)

        set_clause = ", ".join([f"{key} = %({key})s" for key in update_data.keys()])
        query = f"UPDATE crew_members SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %(id)s RETURNING *"

        update_data['id'] = crew_id

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, update_data)
                    result = cursor.fetchone()
                    conn.commit()
                    return CrewMember(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error updating crew member: {e}")

    @log_database_operation
    def set_availability(self, crew_id: int, is_available: bool) -> bool:
        """Встановлення доступності члена екіпажу"""
        query = "UPDATE crew_members SET is_available = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (is_available, crew_id))
                    conn.commit()
                    return cursor.rowcount > 0
        except psycopg2.Error as e:
            raise Exception(f"Database error setting crew availability: {e}")

    # Методи для роботи з посадами
    @log_database_operation
    def get_all_positions(self) -> List[CrewPosition]:
        """Отримання всіх посад екіпажу"""
        query = "SELECT * FROM crew_positions ORDER BY position_name"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query)
                    results = cursor.fetchall()
                    return [CrewPosition(**dict(row)) for row in results]
        except psycopg2.Error as e:
            raise Exception(f"Database error getting crew positions: {e}")

    @log_database_operation
    def find_position_by_id(self, position_id: int) -> Optional[CrewPosition]:
        """Пошук посади за ID"""
        query = "SELECT * FROM crew_positions WHERE id = %s"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (position_id,))
                    result = cursor.fetchone()
                    return CrewPosition(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error finding position by id: {e}")