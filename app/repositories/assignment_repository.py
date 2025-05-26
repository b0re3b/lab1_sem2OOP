from typing import List, Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config.database import DatabaseConfig
from app.config import log_database_operation
from app.models import FlightAssignment
from app.utils.validators import AssignmentValidator


class AssignmentRepository:
    def __init__(self):
        self.table_name = "flight_assignments"
        self.validator = AssignmentValidator()
        self.db_manager = DatabaseConfig()
    @log_database_operation
    def create_assignment(self, assignment_data: Dict[str, Any]) -> Optional[FlightAssignment]:
        """Створення нового призначення"""
        self.validator.validate_assignment_data(assignment_data)

        # Перевіряємо доступність члена екіпажу
        if not self._check_crew_availability(assignment_data['crew_member_id'],
                                             assignment_data['flight_id']):
            raise Exception("Crew member is not available for this flight")

        query = """
                INSERT INTO flight_assignments (flight_id, crew_member_id, assigned_by, status, notes)
                VALUES (%(flight_id)s, %(crew_member_id)s, %(assigned_by)s, %(status)s, %(notes)s) RETURNING * \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, assignment_data)
                    result = cursor.fetchone()
                    conn.commit()
                    return FlightAssignment(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error creating assignment: {e}")

    @log_database_operation
    def find_by_id(self, assignment_id: int) -> Optional[FlightAssignment]:
        """Пошук призначення за ID"""
        query = """
                SELECT fa.*, \
                       f.flight_number, \
                       f.departure_time, \
                       f.arrival_time,
                       cm.first_name || ' ' || cm.last_name as crew_member_name,
                       cp.position_name,
                       u.first_name || ' ' || u.last_name   as assigned_by_name
                FROM flight_assignments fa
                         JOIN flights f ON fa.flight_id = f.id
                         JOIN crew_members cm ON fa.crew_member_id = cm.id
                         JOIN crew_positions cp ON cm.position_id = cp.id
                         JOIN users u ON fa.assigned_by = u.id
                WHERE fa.id = %s \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (assignment_id,))
                    result = cursor.fetchone()
                    return FlightAssignment(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error finding assignment by id: {e}")

    @log_database_operation
    def find_by_flight_id(self, flight_id: int) -> List[FlightAssignment]:
        """Пошук всіх призначень для рейсу"""
        query = """
                SELECT fa.*, \
                       f.flight_number, \
                       f.departure_time, \
                       f.arrival_time,
                       cm.first_name || ' ' || cm.last_name as crew_member_name,
                       cm.employee_id,
                       cp.position_name,
                       u.first_name || ' ' || u.last_name   as assigned_by_name
                FROM flight_assignments fa
                         JOIN flights f ON fa.flight_id = f.id
                         JOIN crew_members cm ON fa.crew_member_id = cm.id
                         JOIN crew_positions cp ON cm.position_id = cp.id
                         JOIN users u ON fa.assigned_by = u.id
                WHERE fa.flight_id = %s \
                  AND fa.status = 'ASSIGNED'
                ORDER BY cp.position_name, cm.last_name \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (flight_id,))
                    results = cursor.fetchall()
                    return [FlightAssignment(**dict(row)) for row in results]
        except psycopg2.Error as e:
            raise Exception(f"Database error finding assignments by flight: {e}")

    @log_database_operation
    def find_by_crew_member_id(self, crew_member_id: int) -> List[FlightAssignment]:
        """Пошук призначень для члена екіпажу"""
        query = """
                SELECT fa.*, \
                       f.flight_number, \
                       f.departure_city, \
                       f.arrival_city,
                       f.departure_time, \
                       f.arrival_time, \
                       f.status                             as flight_status,
                       cm.first_name || ' ' || cm.last_name as crew_member_name,
                       cp.position_name,
                       u.first_name || ' ' || u.last_name   as assigned_by_name
                FROM flight_assignments fa
                         JOIN flights f ON fa.flight_id = f.id
                         JOIN crew_members cm ON fa.crew_member_id = cm.id
                         JOIN crew_positions cp ON cm.position_id = cp.id
                         JOIN users u ON fa.assigned_by = u.id
                WHERE fa.crew_member_id = %s \
                  AND fa.status = 'ASSIGNED'
                ORDER BY f.departure_time \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (crew_member_id,))
                    results = cursor.fetchall()
                    return [FlightAssignment(**dict(row)) for row in results]
        except psycopg2.Error as e:
            raise Exception(f"Database error finding assignments by crew member: {e}")

    @log_database_operation
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[FlightAssignment]:
        """Пошук призначень за період"""
        query = """
                SELECT fa.*, \
                       f.flight_number, \
                       f.departure_city, \
                       f.arrival_city,
                       f.departure_time, \
                       f.arrival_time,
                       cm.first_name || ' ' || cm.last_name as crew_member_name,
                       cp.position_name,
                       u.first_name || ' ' || u.last_name   as assigned_by_name
                FROM flight_assignments fa
                         JOIN flights f ON fa.flight_id = f.id
                         JOIN crew_members cm ON fa.crew_member_id = cm.id
                         JOIN crew_positions cp ON cm.position_id = cp.id
                         JOIN users u ON fa.assigned_by = u.id
                WHERE f.departure_time >= %s \
                  AND f.departure_time <= %s
                  AND fa.status = 'ASSIGNED'
                ORDER BY f.departure_time, f.flight_number \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (start_date, end_date))
                    results = cursor.fetchall()
                    return [FlightAssignment(**dict(row)) for row in results]
        except psycopg2.Error as e:
            raise Exception(f"Database error finding assignments by date range: {e}")

    @log_database_operation
    def update_assignment_status(self, assignment_id: int, status: str, updated_by: int, notes: Optional[str] = None) -> \
    Optional[FlightAssignment]:
        """Оновлення статусу призначення"""
        self.validator.validate_enum_value('status', status, ['ASSIGNED', 'CONFIRMED', 'CANCELLED'])

        query = """
                UPDATE flight_assignments
                SET status     = %s, \
                    notes      = COALESCE(%s, notes), \
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s RETURNING * \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (status, notes, assignment_id))
                    result = cursor.fetchone()
                    conn.commit()
                    return FlightAssignment(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error updating assignment status: {e}")

    @log_database_operation
    def update_assignment(self, assignment_id: int, assignment_data: Dict[str, Any]) -> Optional[FlightAssignment]:
        """Повне оновлення призначення"""
        self.validator.validate_assignment_data(assignment_data)

        # Якщо змінюється член екіпажу або рейс, перевіряємо доступність
        if 'crew_member_id' in assignment_data or 'flight_id' in assignment_data:
            current_assignment = self.find_by_id(assignment_id)
            if not current_assignment:
                raise Exception("Assignment not found")

            crew_member_id = assignment_data.get('crew_member_id', current_assignment.crew_member_id)
            flight_id = assignment_data.get('flight_id', current_assignment.flight_id)

            if not self._check_crew_availability(crew_member_id, flight_id, assignment_id):
                raise Exception("Crew member is not available for this flight")

        # Створюємо динамічний запит на основі переданих полів
        update_fields = []
        params = []

        for field, value in assignment_data.items():
            if field in ['flight_id', 'crew_member_id', 'status', 'notes']:
                update_fields.append(f"{field} = %s")
                params.append(value)

        if not update_fields:
            raise Exception("No valid fields to update")

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(assignment_id)

        query = f"""
            UPDATE flight_assignments 
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING *
        """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    conn.commit()
                    return FlightAssignment(**dict(result)) if result else None
        except psycopg2.Error as e:
            raise Exception(f"Database error updating assignment: {e}")

    @log_database_operation
    def delete_assignment(self, assignment_id: int) -> bool:
        """Видалення призначення"""
        query = "DELETE FROM flight_assignments WHERE id = %s"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (assignment_id,))
                    deleted_rows = cursor.rowcount
                    conn.commit()
                    return deleted_rows > 0
        except psycopg2.Error as e:
            raise Exception(f"Database error deleting assignment: {e}")

    @log_database_operation
    def get_all_assignments(self, page: int = 1, page_size: int = 50, filters: Optional[Dict[str, Any]] = None) -> Dict[
        str, Any]:
        """Отримання всіх призначень з пагінацією та фільтрацією"""
        offset = (page - 1) * page_size
        where_conditions = []
        params = []

        # Застосовуємо фільтри
        if filters:
            if filters.get('status'):
                where_conditions.append("fa.status = %s")
                params.append(filters['status'])

            if filters.get('flight_id'):
                where_conditions.append("fa.flight_id = %s")
                params.append(filters['flight_id'])

            if filters.get('crew_member_id'):
                where_conditions.append("fa.crew_member_id = %s")
                params.append(filters['crew_member_id'])

            if filters.get('date_from'):
                where_conditions.append("f.departure_time >= %s")
                params.append(filters['date_from'])

            if filters.get('date_to'):
                where_conditions.append("f.departure_time <= %s")
                params.append(filters['date_to'])

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Запит для отримання даних
        data_query = f"""
            SELECT fa.*, f.flight_number, f.departure_city, f.arrival_city,
                   f.departure_time, f.arrival_time, f.status as flight_status,
                   cm.first_name || ' ' || cm.last_name as crew_member_name,
                   cm.employee_id,
                   cp.position_name,
                   u.first_name || ' ' || u.last_name as assigned_by_name
            FROM flight_assignments fa
            JOIN flights f ON fa.flight_id = f.id
            JOIN crew_members cm ON fa.crew_member_id = cm.id
            JOIN crew_positions cp ON cm.position_id = cp.id
            JOIN users u ON fa.assigned_by = u.id
            {where_clause}
            ORDER BY f.departure_time DESC, fa.assigned_at DESC
            LIMIT %s OFFSET %s
        """

        # Запит для підрахунку загальної кількості
        count_query = f"""
            SELECT COUNT(*) as total
            FROM flight_assignments fa
            JOIN flights f ON fa.flight_id = f.id
            JOIN crew_members cm ON fa.crew_member_id = cm.id
            {where_clause}
        """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Отримуємо дані
                    cursor.execute(data_query, params + [page_size, offset])
                    assignments = [FlightAssignment(**dict(row)) for row in cursor.fetchall()]

                    # Отримуємо загальну кількість
                    cursor.execute(count_query, params)
                    total_count = cursor.fetchone()['total']

                    return {
                        'assignments': assignments,
                        'total': total_count,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': (total_count + page_size - 1) // page_size
                    }
        except psycopg2.Error as e:
            raise Exception(f"Database error getting assignments: {e}")

    @log_database_operation
    def get_flight_crew_statistics(self, flight_id: int) -> Dict[str, Any]:
        """Отримання статистики екіпажу для рейсу"""
        query = """
                SELECT f.id         as flight_id, \
                       f.flight_number, \
                       f.crew_required, \
                       COUNT(fa.id) as assigned_count, \
                       CASE \
                           WHEN COUNT(fa.id) >= f.crew_required THEN 'FULLY_STAFFED' \
                           WHEN COUNT(fa.id) > 0 THEN 'PARTIALLY_STAFFED' \
                           ELSE 'NOT_STAFFED' \
                           END      as staffing_status, \
                       ARRAY_AGG( \
                               CASE \
                                   WHEN fa.id IS NOT NULL THEN \
                                       JSON_BUILD_OBJECT( \
                                               'crew_member_id', cm.id, \
                                               'name', cm.first_name || ' ' || cm.last_name, \
                                               'position', cp.position_name, \
                                               'experience_years', cm.experience_years \
                                       ) \
                                   END \
                       )               FILTER (WHERE fa.id IS NOT NULL) as assigned_crew
                FROM flights f
                         LEFT JOIN flight_assignments fa ON f.id = fa.flight_id AND fa.status = 'ASSIGNED'
                         LEFT JOIN crew_members cm ON fa.crew_member_id = cm.id
                         LEFT JOIN crew_positions cp ON cm.position_id = cp.id
                WHERE f.id = %s
                GROUP BY f.id, f.flight_number, f.crew_required \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (flight_id,))
                    result = cursor.fetchone()
                    return dict(result) if result else {}
        except psycopg2.Error as e:
            raise Exception(f"Database error getting flight crew statistics: {e}")

    @log_database_operation
    def get_crew_member_workload(self, crew_member_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Отримання навантаження члена екіпажу за період"""
        query = """
                SELECT cm.id                                                               as crew_member_id, \
                       cm.first_name || ' ' || cm.last_name                                as name, \
                       cp.position_name, \
                       COUNT(fa.id)                                                        as total_flights, \
                       SUM(EXTRACT(EPOCH FROM (f.arrival_time - f.departure_time)) / 3600) as total_flight_hours, \
                       ARRAY_AGG( \
                               JSON_BUILD_OBJECT( \
                                       'flight_number', f.flight_number, \
                                       'departure_time', f.departure_time, \
                                       'arrival_time', f.arrival_time, \
                                       'route', f.departure_city || ' - ' || f.arrival_city \
                               ) ORDER BY f.departure_time \
                       )                                                                   as flights
                FROM crew_members cm
                         JOIN crew_positions cp ON cm.position_id = cp.id
                         LEFT JOIN flight_assignments fa ON cm.id = fa.crew_member_id AND fa.status = 'ASSIGNED'
                         LEFT JOIN flights f ON fa.flight_id = f.id
                    AND f.departure_time >= %s AND f.departure_time <= %s
                WHERE cm.id = %s
                GROUP BY cm.id, cm.first_name, cm.last_name, cp.position_name \
                """

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (start_date, end_date, crew_member_id))
                    result = cursor.fetchone()
                    return dict(result) if result else {}
        except psycopg2.Error as e:
            raise Exception(f"Database error getting crew member workload: {e}")

    def _check_crew_availability(self, crew_member_id: int, flight_id: int,
                                 exclude_assignment_id: Optional[int] = None) -> bool:
        """Приватний метод для перевірки доступності члена екіпажу"""
        # Отримуємо інформацію про рейс
        flight_query = "SELECT departure_time, arrival_time FROM flights WHERE id = %s"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(flight_query, (flight_id,))
                    flight = cursor.fetchone()

                    if not flight:
                        return False

                    # Використовуємо функцію БД для перевірки доступності
                    availability_query = "SELECT check_crew_availability(%s, %s, %s) as available"
                    cursor.execute(availability_query,
                                   (crew_member_id, flight['departure_time'], flight['arrival_time']))
                    result = cursor.fetchone()

                    # Додаткова перевірка для випадку оновлення існуючого призначення
                    if exclude_assignment_id:
                        conflict_query = """
                                         SELECT COUNT(*) as conflicts
                                         FROM flight_assignments fa
                                                  JOIN flights f ON fa.flight_id = f.id
                                         WHERE fa.crew_member_id = %s
                                           AND fa.status = 'ASSIGNED'
                                           AND fa.id != %s
                                           AND (
                                             (f.departure_time <= %s \
                                           AND f.arrival_time >= %s)
                                            OR
                                             (f.departure_time <= %s \
                                           AND f.arrival_time >= %s)
                                            OR
                                             (f.departure_time >= %s \
                                           AND f.arrival_time <= %s)
                                             ) \
                                         """
                        cursor.execute(conflict_query, (
                            crew_member_id, exclude_assignment_id,
                            flight['departure_time'], flight['departure_time'],
                            flight['arrival_time'], flight['arrival_time'],
                            flight['departure_time'], flight['arrival_time']
                        ))
                        conflicts = cursor.fetchone()['conflicts']
                        return conflicts == 0

                    return result['available'] if result else False

        except psycopg2.Error as e:
            raise Exception(f"Database error checking crew availability: {e}")