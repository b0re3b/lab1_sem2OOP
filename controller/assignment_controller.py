from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from utils.decorators import AuthDecorators
from ..config.logging_config import log_info, log_error, log_access
from ..middleware.auth_middleware import get_current_user
from ..models.flight_assignment import FlightAssignment
from ..services.assignment_service import AssignmentService
from ..utils.validators import AssignmentValidator, ValidationError

jwt_required = AuthDecorators()
role_required = AuthDecorators()
admin_required = AuthDecorators()
dispatcher_required = AuthDecorators()
# Pydantic моделі для запитів та відповідей
class CreateAssignmentRequest(BaseModel):
    flight_id: int = Field(..., description="ID рейсу")
    crew_member_id: int = Field(..., description="ID члена екіпажу")
    notes: Optional[str] = Field(None, max_length=500, description="Додаткові примітки")


class UpdateAssignmentRequest(BaseModel):
    status: Optional[str] = Field(None, description="Новий статус призначення")
    notes: Optional[str] = Field(None, max_length=500, description="Оновлені примітки")


class AutoAssignRequest(BaseModel):
    flight_id: int = Field(..., description="ID рейсу для автоматичного призначення")
    preferred_positions: Optional[List[str]] = Field(None, description="Пріоритетні позиції")


class AssignmentSummaryResponse(BaseModel):
    total_assignments: int
    active_assignments: int
    cancelled_assignments: int
    confirmed_assignments: int


class CrewWorkloadResponse(BaseModel):
    crew_member_id: int
    crew_member_name: str
    position: str
    total_assignments: int
    upcoming_flights: int
    workload_percentage: float


class FlightCrewStatisticsResponse(BaseModel):
    flight_id: int
    flight_number: str
    required_crew: int
    assigned_crew: int
    confirmed_crew: int
    staffing_percentage: float
    missing_positions: List[str]


# Створення роутера
router = APIRouter(prefix="/api/assignments", tags=["Assignments"])

# Ініціалізація сервісу
assignment_service = AssignmentService()


@router.post("/",
             status_code=status.HTTP_201_CREATED,
             response_model=FlightAssignment,
             summary="Створити нове призначення екіпажу")
def create_assignment(
        request: CreateAssignmentRequest,
        current_user=Depends(get_current_user)
):
    """
    Створити нове призначення члена екіпажу на рейс.

    Потрібні права: DISPATCHER або ADMIN
    """
    try:
        # Валідація даних
        AssignmentValidator.validate_assignment_data({
            'flight_id': request.flight_id,
            'crew_member_id': request.crew_member_id
        })

        # Створення призначення
        assignment = assignment_service.create_assignment(
            flight_id=request.flight_id,
            crew_member_id=request.crew_member_id,
            assigned_by=current_user.id,
            notes=request.notes
        )

        log_info(f"Assignment created: {assignment.id} by user {current_user.username}")
        log_access(f"POST /assignments - Assignment created for flight {request.flight_id}")

        return assignment

    except ValidationError as e:
        log_error(f"Validation error in create_assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Помилка валідації: {str(e)}"
        )
    except Exception as e:
        log_error(f"Error creating assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка створення призначення"
        )


@router.get("/{assignment_id}",
            response_model=FlightAssignment,
            summary="Отримати призначення за ID")
def get_assignment(
        assignment_id: int,
        current_user=Depends(get_current_user)
):
    """
    Отримати деталі призначення за його ID.

    Потрібні права: будь-який аутентифікований користувач
    """
    try:
        assignment = assignment_service.get_assignment_by_id(assignment_id)

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Призначення не знайдено"
            )

        log_access(f"GET /assignments/{assignment_id} - Assignment viewed by {current_user.username}")
        return assignment

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error getting assignment {assignment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання призначення"
        )


@router.get("/",
            response_model=List[FlightAssignment],
            summary="Отримати список всіх призначень")
@jwt_required
def get_all_assignments(
        current_user=Depends(get_current_user),
        skip: int = Query(0, ge=0, description="Кількість записів для пропуску"),
        limit: int = Query(100, ge=1, le=1000, description="Максимальна кількість записів"),
        status_filter: Optional[str] = Query(None, description="Фільтр за статусом"),
        flight_id: Optional[int] = Query(None, description="Фільтр за ID рейсу"),
        crew_member_id: Optional[int] = Query(None, description="Фільтр за ID члена екіпажу")
):
    """
    Отримати список призначень з можливістю фільтрації та пагінації.

    Потрібні права: будь-який аутентифікований користувач
    """
    try:
        assignments = assignment_service.get_all_assignments(
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            flight_id=flight_id,
            crew_member_id=crew_member_id
        )

        log_access(f"GET /assignments - {len(assignments)} assignments retrieved by {current_user.username}")
        return assignments

    except Exception as e:
        log_error(f"Error getting assignments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання списку призначень"
        )


@router.get("/flight/{flight_id}",
            response_model=List[FlightAssignment],
            summary="Отримати призначення для конкретного рейсу")
@jwt_required
def get_assignments_by_flight(
        flight_id: int,
        current_user=Depends(get_current_user)
):
    """
    Отримати всі призначення для конкретного рейсу.

    Потрібні права: будь-який аутентифікований користувач
    """
    try:
        assignments = assignment_service.get_assignments_by_flight(flight_id)

        log_access(f"GET /assignments/flight/{flight_id} - {len(assignments)} assignments retrieved")
        return assignments

    except Exception as e:
        log_error(f"Error getting assignments for flight {flight_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання призначень для рейсу"
        )


@router.get("/crew/{crew_member_id}",
            response_model=List[FlightAssignment],
            summary="Отримати призначення для конкретного члена екіпажу")
@jwt_required
def get_assignments_by_crew_member(
        crew_member_id: int,
        current_user=Depends(get_current_user)
):
    """
    Отримати всі призначення для конкретного члена екіпажу.

    Потрібні права: будь-який аутентифікований користувач
    """
    try:
        assignments = assignment_service.get_assignments_by_crew_member(crew_member_id)

        log_access(f"GET /assignments/crew/{crew_member_id} - {len(assignments)} assignments retrieved")
        return assignments

    except Exception as e:
        log_error(f"Error getting assignments for crew member {crew_member_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання призначень для члена екіпажу"
        )


@router.get("/date-range",
            response_model=List[FlightAssignment],
            summary="Отримати призначення за період")
@jwt_required
def get_assignments_by_date_range(
        start_date: date = Query(..., description="Початкова дата (YYYY-MM-DD)"),
        end_date: date = Query(..., description="Кінцева дата (YYYY-MM-DD)"),
        current_user=Depends(get_current_user)
):
    """
    Отримати призначення за вказаний період часу.

    Потрібні права: будь-який аутентифікований користувач
    """
    try:
        # Валідація діапазону дат
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Початкова дата не може бути пізніше кінцевої"
            )

        assignments = assignment_service.get_assignments_by_date_range(start_date, end_date)

        log_access(
            f"GET /assignments/date-range - {len(assignments)} assignments retrieved for period {start_date} to {end_date}")
        return assignments

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error getting assignments by date range: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання призначень за період"
        )


@router.put("/{assignment_id}",
            response_model=FlightAssignment,
            summary="Оновити призначення")
@dispatcher_required
def update_assignment(
        assignment_id: int,
        request: UpdateAssignmentRequest,
        current_user=Depends(get_current_user)
):
    """
    Оновити існуюче призначення.

    Потрібні права: DISPATCHER або ADMIN
    """
    try:
        # Перевірка існування призначення
        existing_assignment = assignment_service.get_assignment_by_id(assignment_id)
        if not existing_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Призначення не знайдено"
            )

        # Оновлення призначення
        updated_assignment = assignment_service.update_assignment(
            assignment_id=assignment_id,
            status=request.status,
            notes=request.notes
        )

        log_info(f"Assignment {assignment_id} updated by user {current_user.username}")
        log_access(f"PUT /assignments/{assignment_id} - Assignment updated")

        return updated_assignment

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error updating assignment {assignment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка оновлення призначення"
        )


@router.delete("/{assignment_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Скасувати призначення")
@dispatcher_required
def cancel_assignment(
        assignment_id: int,
        current_user=Depends(get_current_user)
):
    """
    Скасувати призначення (встановити статус CANCELLED).

    Потрібні права: DISPATCHER або ADMIN
    """
    try:
        # Перевірка існування призначення
        existing_assignment = assignment_service.get_assignment_by_id(assignment_id)
        if not existing_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Призначення не знайдено"
            )

        # Скасування призначення
        assignment_service.cancel_assignment(assignment_id)

        log_info(f"Assignment {assignment_id} cancelled by user {current_user.username}")
        log_access(f"DELETE /assignments/{assignment_id} - Assignment cancelled")

        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content={"message": "Призначення успішно скасовано"}
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error cancelling assignment {assignment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка скасування призначення"
        )


@router.post("/auto-assign",
             response_model=List[FlightAssignment],
             summary="Автоматичне призначення екіпажу")
@dispatcher_required
def auto_assign_crew(
        request: AutoAssignRequest,
        current_user=Depends(get_current_user)
):
    """
    Автоматично призначити доступний екіпаж на рейс.

    Потрібні права: DISPATCHER або ADMIN
    """
    try:
        assignments = assignment_service.auto_assign_crew(
            flight_id=request.flight_id,
            assigned_by=current_user.id,
            preferred_positions=request.preferred_positions
        )

        log_info(f"Auto-assignment completed for flight {request.flight_id}: {len(assignments)} assignments created")
        log_access(f"POST /assignments/auto-assign - {len(assignments)} auto-assignments created")

        return assignments

    except Exception as e:
        log_error(f"Error in auto-assignment for flight {request.flight_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка автоматичного призначення екіпажу"
        )


@router.get("/statistics/summary",
            response_model=AssignmentSummaryResponse,
            summary="Загальна статистика призначень")
@jwt_required
def get_assignment_summary(
        current_user=Depends(get_current_user)
):
    """
    Отримати загальну статистику по призначеннях.

    Потрібні права: будь-який аутентифікований користувач
    """
    try:
        summary = assignment_service.get_assignment_summary()

        log_access(f"GET /assignments/statistics/summary - Statistics retrieved by {current_user.username}")
        return summary

    except Exception as e:
        log_error(f"Error getting assignment summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання статистики призначень"
        )


@router.get("/statistics/crew-workload",
            response_model=List[CrewWorkloadResponse],
            summary="Статистика навантаження екіпажу")
@jwt_required
def get_crew_workload_statistics(
        current_user=Depends(get_current_user),
        start_date: Optional[date] = Query(None, description="Початкова дата для аналізу"),
        end_date: Optional[date] = Query(None, description="Кінцева дата для аналізу")
):
    """
    Отримати статистику навантаження членів екіпажу.

    Потрібні права: будь-який аутентифікований користувач
    """
    try:
        workload_stats = assignment_service.get_crew_member_workload(
            start_date=start_date,
            end_date=end_date
        )

        log_access(f"GET /assignments/statistics/crew-workload - Workload statistics retrieved")
        return workload_stats

    except Exception as e:
        log_error(f"Error getting crew workload statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання статистики навантаження екіпажу"
        )


@router.get("/statistics/flight-crew",
            response_model=List[FlightCrewStatisticsResponse],
            summary="Статистика укомплектованості рейсів")
@jwt_required
def get_flight_crew_statistics(
        current_user=Depends(get_current_user),
        start_date: Optional[date] = Query(None, description="Початкова дата"),
        end_date: Optional[date] = Query(None, description="Кінцева дата"),
        status_filter: Optional[str] = Query(None, description="Фільтр за статусом рейсу")
):
    """
    Отримати статистику укомплектованості рейсів екіпажем.

    Потрібні права: будь-який аутентифікований користувач
    """
    try:
        flight_stats = assignment_service.get_flight_crew_statistics(
            start_date=start_date,
            end_date=end_date,
            status_filter=status_filter
        )

        log_access(f"GET /assignments/statistics/flight-crew - Flight crew statistics retrieved")
        return flight_stats

    except Exception as e:
        log_error(f"Error getting flight crew statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання статистики укомплектованості рейсів"
        )


@router.get("/available-crew/{flight_id}",
            response_model=List[dict],
            summary="Отримати доступний екіпаж для рейсу")
@jwt_required
def get_available_crew_for_flight(
        flight_id: int,
        current_user=Depends(get_current_user)
):
    """
    Отримати список доступних членів екіпажу для конкретного рейсу.

    Потрібні права: будь-який аутентифікований користувач
    """
    try:
        available_crew = assignment_service.get_available_crew_for_flight(flight_id)

        log_access(f"GET /assignments/available-crew/{flight_id} - Available crew retrieved")
        return available_crew

    except Exception as e:
        log_error(f"Error getting available crew for flight {flight_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання доступного екіпажу"
        )


@router.post("/{assignment_id}/confirm",
             response_model=FlightAssignment,
             summary="Підтвердити призначення")
@dispatcher_required
def confirm_assignment(
        assignment_id: int,
        current_user=Depends(get_current_user)
):
    """
    Підтвердити призначення (встановити статус CONFIRMED).

    Потрібні права: DISPATCHER або ADMIN
    """
    try:
        # Перевірка існування призначення
        existing_assignment = assignment_service.get_assignment_by_id(assignment_id)
        if not existing_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Призначення не знайдено"
            )

        # Підтвердження призначення
        confirmed_assignment = assignment_service.update_assignment(
            assignment_id=assignment_id,
            status='CONFIRMED'
        )

        log_info(f"Assignment {assignment_id} confirmed by user {current_user.username}")
        log_access(f"POST /assignments/{assignment_id}/confirm - Assignment confirmed")

        return confirmed_assignment

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error confirming assignment {assignment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка підтвердження призначення"
        )


# Обробка помилок на рівні роутера
@router.exception_handler(ValidationError)
def validation_error_handler(request, exc):
    """Обробник помилок валідації"""
    log_error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": f"Помилка валідації: {str(exc)}"}
    )


@router.exception_handler(Exception)
def general_error_handler(request, exc):
    """Загальний обробник помилок"""
    log_error(f"Unexpected error in assignment controller: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутрішня помилка сервера"}
    )