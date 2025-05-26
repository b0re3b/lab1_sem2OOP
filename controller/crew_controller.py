from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from utils.decorators import ErrorHandlingDecorators
from ..config.logging_config import log_info, log_error
from ..services.crew_service import CrewService
from ..utils.decorators import AuthDecorators
from ..utils.validators import CrewValidator, ValidationError

router = APIRouter(prefix="/api/crew", tags=["crew"])
crew_service = CrewService()
jwt_required = AuthDecorators.jwt_required
role_required = AuthDecorators.role_required
handle_exceptions = ErrorHandlingDecorators.handle_exceptions

@router.post("/members", response_model=dict, status_code=status.HTTP_201_CREATED)
@handle_exceptions
@jwt_required
@role_required(["ADMIN"])
def create_crew_member(crew_data: dict, current_user=Depends()):
    """
    Створити нового члена екіпажу (тільки для адміністраторів)
    """
    try:
        # Валідація даних
        CrewValidator.validate_crew_member_data(crew_data)

        # Створення члена екіпажу
        crew_member = crew_service.create_crew_member(crew_data)

        log_info(f"Created crew member: {crew_member.employee_id} by user {current_user['id']}")

        return {
            "status": "success",
            "message": "Член екіпажу успішно створений",
            "data": crew_member.dict()
        }

    except ValidationError as e:
        log_error(f"Validation error creating crew member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Помилка валідації: {str(e)}"
        )
    except Exception as e:
        log_error(f"Error creating crew member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка створення члена екіпажу"
        )


@router.get("/members/{crew_id}", response_model=dict)
@handle_exceptions
@jwt_required
def get_crew_member(crew_id: int, current_user=Depends()):
    """
    Отримати інформацію про конкретного члена екіпажу
    """
    try:
        crew_member = crew_service.get_crew_member_by_id(crew_id)

        if not crew_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Член екіпажу не знайдений"
            )

        return {
            "status": "success",
            "data": crew_member.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error getting crew member {crew_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання інформації про члена екіпажу"
        )


@router.get("/members/employee/{employee_id}", response_model=dict)
@handle_exceptions
@jwt_required
def get_crew_member_by_employee_id(employee_id: str, current_user=Depends()):
    """
    Отримати члена екіпажу за службовим номером
    """
    try:
        crew_member = crew_service.get_crew_member_by_employee_id(employee_id)

        if not crew_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Член екіпажу з таким службовим номером не знайдений"
            )

        return {
            "status": "success",
            "data": crew_member.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error getting crew member by employee ID {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання інформації про члена екіпажу"
        )


@router.get("/members/available", response_model=dict)
@handle_exceptions
@jwt_required
def get_available_crew(
        position_id: Optional[int] = Query(None, description="ID посади для фільтрації"),
        flight_id: Optional[int] = Query(None, description="ID рейсу для перевірки доступності"),
        current_user=Depends()
):
    """
    Отримати список доступних членів екіпажу
    """
    try:
        if flight_id:
            # Отримати доступний екіпаж для конкретного рейсу
            available_crew = crew_service.get_available_crew_for_flight(flight_id)
        elif position_id:
            # Отримати доступний екіпаж за посадою
            available_crew = crew_service.get_available_crew_by_position(position_id)
        else:
            # Отримати весь доступний екіпаж
            available_crew = crew_service.get_available_crew_by_position(None)

        return {
            "status": "success",
            "data": [crew.dict() for crew in available_crew],
            "count": len(available_crew)
        }

    except Exception as e:
        log_error(f"Error getting available crew: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання списку доступного екіпажу"
        )


@router.put("/members/{crew_id}", response_model=dict)
@handle_exceptions
@jwt_required
@role_required(["ADMIN"])
def update_crew_member(crew_id: int, crew_data: dict, current_user=Depends()):
    """
    Оновити інформацію про члена екіпажу (тільки для адміністраторів)
    """
    try:
        # Валідація даних
        CrewValidator.validate_crew_member_data(crew_data)

        # Оновлення члена екіпажу
        updated_crew = crew_service.update_crew_member(crew_id, crew_data)

        if not updated_crew:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Член екіпажу не знайдений"
            )

        log_info(f"Updated crew member {crew_id} by user {current_user['id']}")

        return {
            "status": "success",
            "message": "Інформацію про члена екіпажу оновлено",
            "data": updated_crew.dict()
        }

    except ValidationError as e:
        log_error(f"Validation error updating crew member {crew_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Помилка валідації: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error updating crew member {crew_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка оновлення інформації про члена екіпажу"
        )


@router.patch("/members/{crew_id}/availability", response_model=dict)
@handle_exceptions
@jwt_required
@role_required(["ADMIN", "DISPATCHER"])
def set_crew_availability(
        crew_id: int,
        availability_data: dict,
        current_user=Depends()
):
    """
    Встановити доступність члена екіпажу
    """
    try:
        is_available = availability_data.get("is_available")
        if is_available is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Поле 'is_available' є обов'язковим"
            )

        success = crew_service.set_crew_availability(crew_id, is_available)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Член екіпажу не знайдений"
            )

        log_info(f"Set crew {crew_id} availability to {is_available} by user {current_user['id']}")

        return {
            "status": "success",
            "message": f"Доступність члена екіпажу {'увімкнено' if is_available else 'вимкнено'}"
        }

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error setting crew availability {crew_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка встановлення доступності члена екіпажу"
        )


@router.get("/positions", response_model=dict)
@handle_exceptions
@jwt_required
def get_all_positions(current_user=Depends()):
    """
    Отримати список всіх посад екіпажу
    """
    try:
        positions = crew_service.get_all_positions()

        return {
            "status": "success",
            "data": [position.dict() for position in positions],
            "count": len(positions)
        }

    except Exception as e:
        log_error(f"Error getting positions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання списку посад"
        )


@router.get("/positions/{position_id}", response_model=dict)
@handle_exceptions
@jwt_required
def get_position(position_id: int, current_user=Depends()):
    """
    Отримати інформацію про конкретну посаду
    """
    try:
        position = crew_service.get_position_by_id(position_id)

        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Посада не знайдена"
            )

        return {
            "status": "success",
            "data": position.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error getting position {position_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання інформації про посаду"
        )


@router.get("/statistics/workload", response_model=dict)
@handle_exceptions
@jwt_required
@role_required(["ADMIN"])
def get_crew_workload_statistics(
        start_date: Optional[date] = Query(None, description="Початкова дата"),
        end_date: Optional[date] = Query(None, description="Кінцева дата"),
        current_user=Depends()
):
    """
    Отримати статистику навантаження екіпажу (тільки для адміністраторів)
    """
    try:
        statistics = crew_service.get_crew_workload_statistics(start_date, end_date)

        return {
            "status": "success",
            "data": statistics,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }

    except Exception as e:
        log_error(f"Error getting crew workload statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання статистики навантаження екіпажу"
        )


@router.get("/members/{crew_id}/availability", response_model=dict)
@handle_exceptions
@jwt_required
def check_crew_member_availability(
        crew_id: int,
        flight_departure: datetime = Query(..., description="Час вильоту"),
        flight_arrival: datetime = Query(..., description="Час прибуття"),
        current_user=Depends()
):
    """
    Перевірити доступність члена екіпажу для конкретного часового проміжку
    """
    try:
        is_available = crew_service.check_crew_member_availability(
            crew_id, flight_departure, flight_arrival
        )

        return {
            "status": "success",
            "data": {
                "crew_member_id": crew_id,
                "is_available": is_available,
                "period": {
                    "departure": flight_departure.isoformat(),
                    "arrival": flight_arrival.isoformat()
                }
            }
        }

    except Exception as e:
        log_error(f"Error checking crew availability {crew_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка перевірки доступності члена екіпажу"
        )


@router.get("/recommendations/{flight_id}", response_model=dict)
@handle_exceptions
@jwt_required
@role_required(["ADMIN", "DISPATCHER"])
def get_crew_recommendations(flight_id: int, current_user=Depends()):
    """
    Отримати рекомендації щодо призначення екіпажу для рейсу
    """
    try:
        recommendations = crew_service.get_crew_recommendations_for_flight(flight_id)

        return {
            "status": "success",
            "data": recommendations,
            "flight_id": flight_id
        }

    except Exception as e:
        log_error(f"Error getting crew recommendations for flight {flight_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка отримання рекомендацій щодо екіпажу"
        )