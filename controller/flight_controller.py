import logging
from datetime import datetime, date
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, validator

from .auth_controller import get_current_user_dep
from ..models.flight import Flight
from ..models.user import User
from ..services.flight_service import FlightService
from ..utils.decorators import AuthDecorators, LoggingDecorators, ErrorHandlingDecorators, ValidationDecorators
from ..utils.validators import FlightValidator, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/flights", tags=["Рейси"])

log_execution = LoggingDecorators.log_execution
handle_exceptions = ErrorHandlingDecorators.handle_exceptions
validate_input = ValidationDecorators.validate_input
role_required = AuthDecorators.role_required

# Моделі запитів/відповідей
class CreateFlightRequest(BaseModel):
    flight_number: str
    departure_city: str
    arrival_city: str
    departure_time: datetime
    arrival_time: datetime
    aircraft_type: str
    crew_required: int = 4

    @validator('departure_time', 'arrival_time')
    def validate_times(cls, v):
        if v < datetime.now():
            raise ValueError('Час рейсу не може бути в минулому')
        return v

    @validator('arrival_time')
    def validate_arrival_after_departure(cls, v, values):
        if 'departure_time' in values and v <= values['departure_time']:
            raise ValueError('Час прибуття повинен бути після часу відправлення')
        return v


class UpdateFlightRequest(BaseModel):
    departure_city: Optional[str] = None
    arrival_city: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    aircraft_type: Optional[str] = None
    crew_required: Optional[int] = None
    status: Optional[str] = None


class FlightResponse(BaseModel):
    flight: Flight
    crew_summary: Optional[dict] = None


class FlightListResponse(BaseModel):
    flights: List[Flight]
    total: int
    page: int
    size: int


class FlightScheduleResponse(BaseModel):
    date: date
    flights: List[Flight]
    total_flights: int
    flights_by_status: dict


# Залежності
def get_flight_service() -> FlightService:
    return FlightService()


@router.post("/", response_model=FlightResponse, status_code=status.HTTP_201_CREATED)
@log_execution
@handle_exceptions
@role_required(["ADMIN", "DISPATCHER"])
def create_flight(
        request: CreateFlightRequest,
        current_user: User = Depends(get_current_user_dep),
        flight_service: FlightService = Depends(get_flight_service)
):
    """
    Створення нового рейсу (тільки для адміністратора/диспетчера)
    """
    try:
        # Валідація даних рейсу
        FlightValidator.validate_flight_data(request.dict())

        flight_data = request.dict()
        flight_data['created_by'] = current_user.id

        flight =  flight_service.create_flight(flight_data)
        crew_summary =  flight_service.get_flight_crew_summary(flight.id)

        return FlightResponse(flight=flight, crew_summary=crew_summary)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Помилка при створенні рейсу: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося створити рейс"
        )


@router.get("/{flight_id}", response_model=FlightResponse)
@log_execution
@handle_exceptions
def get_flight(
        flight_id: int,
        include_crew: bool = Query(False, description="Включити інформацію про екіпаж"),
        current_user: User = Depends(get_current_user_dep),
        flight_service: FlightService = Depends(get_flight_service)
):
    """
    Отримання рейсу за ID
    """
    try:
        flight =  flight_service.get_flight_by_id(flight_id)
        if not flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Рейс не знайдено"
            )

        crew_summary = None
        if include_crew:
            crew_summary =  flight_service.get_flight_crew_summary(flight_id)

        return FlightResponse(flight=flight, crew_summary=crew_summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при отриманні рейсу: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося отримати рейс"
        )


@router.get("/number/{flight_number}", response_model=FlightResponse)
@log_execution
@handle_exceptions
def get_flight_by_number(
        flight_number: str,
        current_user: User = Depends(get_current_user_dep),
        flight_service: FlightService = Depends(get_flight_service)
):
    """
    Отримання рейсу за номером рейсу
    """
    try:
        flight =  flight_service.get_flight_by_number(flight_number)
        if not flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Рейс не знайдено"
            )

        crew_summary =  flight_service.get_flight_crew_summary(flight.id)
        return FlightResponse(flight=flight, crew_summary=crew_summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при отриманні рейсу за номером: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося отримати рейс"
        )


@router.get("/", response_model=FlightListResponse)
@log_execution
@handle_exceptions
def get_flights(
        page: int = Query(1, ge=1, description="Номер сторінки"),
        size: int = Query(20, ge=1, le=100, description="Розмір сторінки"),
        status_filter: Optional[str] = Query(None, description="Фільтр за статусом"),
        departure_city: Optional[str] = Query(None, description="Фільтр за містом відправлення"),
        arrival_city: Optional[str] = Query(None, description="Фільтр за містом прибуття"),
        from_date: Optional[date] = Query(None, description="Фільтр рейсів від дати"),
        to_date: Optional[date] = Query(None, description="Фільтр рейсів до дати"),
        current_user: User = Depends(get_current_user_dep),
        flight_service: FlightService = Depends(get_flight_service)
):
    """
    Отримання сторінкованого списку рейсів з фільтрами
    """
    try:
        filters = {}
        if status_filter:
            filters['status'] = status_filter
        if departure_city:
            filters['departure_city'] = departure_city
        if arrival_city:
            filters['arrival_city'] = arrival_city

        if from_date and to_date:
            flights =  flight_service.get_flights_by_date_range(from_date, to_date, filters)
        elif status_filter:
            flights =  flight_service.get_flights_by_status(status_filter)
        else:
            flights =  flight_service.get_all_flights(page, size, filters)

        total = len(flights) if isinstance(flights, list) else flights.get('total', 0)
        flight_list = flights if isinstance(flights, list) else flights.get('flights', [])

        return FlightListResponse(
            flights=flight_list,
            total=total,
            page=page,
            size=size
        )

    except Exception as e:
        logger.error(f"Помилка при отриманні списку рейсів: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося отримати список рейсів"
        )


@router.get("/needing-crew/list", response_model=List[Flight])
@log_execution
@handle_exceptions
def get_flights_needing_crew(
        current_user: User = Depends(get_current_user_dep),
        flight_service: FlightService = Depends(get_flight_service)
):
    """
    Отримання рейсів, які потребують призначення екіпажу
    """
    try:
        flights =  flight_service.get_flights_needing_crew()
        return flights

    except Exception as e:
        logger.error(f"Помилка при отриманні рейсів, які потребують екіпажу: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося отримати список рейсів, які потребують екіпажу"
        )


@router.get("/schedule/daily", response_model=FlightScheduleResponse)
@log_execution
@handle_exceptions
def get_daily_schedule(
        target_date: date = Query(..., description="Дата для розкладу"),
        current_user: User = Depends(get_current_user_dep),
        flight_service: FlightService = Depends(get_flight_service)
):
    """
    Отримання щоденного розкладу рейсів
    """
    try:
        schedule =  flight_service.get_daily_flight_schedule(target_date)
        return FlightScheduleResponse(**schedule)

    except Exception as e:
        logger.error(f"Помилка при отриманні щоденного розкладу: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося отримати щоденний розклад"
        )


@router.put("/{flight_id}", response_model=FlightResponse)
@log_execution
@handle_exceptions
@role_required(["ADMIN", "DISPATCHER"])
def update_flight(
        flight_id: int,
        request: UpdateFlightRequest,
        current_user: User = Depends(get_current_user_dep),
        flight_service: FlightService = Depends(get_flight_service)
):
    """
    Оновлення інформації про рейс (тільки для адміністратора/диспетчера)
    """
    try:
        # Перевірка існування рейсу
        existing_flight =  flight_service.get_flight_by_id(flight_id)
        if not existing_flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Рейс не знайдено"
            )

        # Валідація даних для оновлення
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        if update_data:
            FlightValidator.validate_flight_data(update_data, partial=True)

        updated_flight =  flight_service.update_flight(flight_id, update_data)
        crew_summary =  flight_service.get_flight_crew_summary(flight_id)

        return FlightResponse(flight=updated_flight, crew_summary=crew_summary)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при оновленні рейсу: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося оновити рейс"
        )


@router.patch("/{flight_id}/status")
@log_execution
@handle_exceptions
@role_required(["ADMIN", "DISPATCHER"])
def update_flight_status(
        flight_id: int,
        new_status: str = Query(..., description="Новий статус рейсу"),
        current_user: User = Depends(get_current_user_dep),
        flight_service: FlightService = Depends(get_flight_service)
):
    """
    Оновлення статусу рейсу (тільки для адміністратора/диспетчера)
    """
    try:
        # Валідація статусу
        valid_statuses = ['SCHEDULED', 'DELAYED', 'CANCELLED', 'COMPLETED']
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Невірний статус. Має бути один з: {', '.join(valid_statuses)}"
            )

        updated_flight =  flight_service.update_flight_status(flight_id, new_status)
        if not updated_flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Рейс не знайдено"
            )

        return {"message": f"Статус рейсу оновлено до {new_status}", "flight": updated_flight}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при оновленні статусу рейсу: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося оновити статус рейсу"
        )


@router.delete("/{flight_id}")
@log_execution
@handle_exceptions
@role_required(["ADMIN"])
def delete_flight(
        flight_id: int,
        current_user: User = Depends(get_current_user_dep),
        flight_service: FlightService = Depends(get_flight_service)
):
    """
    Видалення рейсу (тільки для адміністратора)
    """
    try:
        # Перевірка існування рейсу
        existing_flight =  flight_service.get_flight_by_id(flight_id)
        if not existing_flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Рейс не знайдено"
            )

        # Перевірка наявності призначень екіпажу
        crew_summary =  flight_service.get_flight_crew_summary(flight_id)
        if crew_summary and crew_summary.get('assigned_crew_count', 0) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неможливо видалити рейс з призначеним екіпажем. Спочатку скасуйте призначення."
            )

        success =  flight_service.delete_flight(flight_id)
        if success:
            return {"message": "Рейс успішно видалено"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не вдалося видалити рейс"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при видаленні рейсу: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося видалити рейс"
        )


@router.get("/{flight_id}/crew-summary")
@log_execution
@handle_exceptions
def get_flight_crew_summary(
        flight_id: int,
        current_user: User = Depends(get_current_user_dep),
        flight_service: FlightService = Depends(get_flight_service)
):
    """
    Отримання зведеної інформації про екіпаж для конкретного рейсу
    """
    try:
        # Перевірка існування рейсу
        flight =  flight_service.get_flight_by_id(flight_id)
        if not flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Рейс не знайдено"
            )

        crew_summary =  flight_service.get_flight_crew_summary(flight_id)
        return crew_summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при отриманні зведеної інформації про екіпаж: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося отримати зведену інформацію про екіпаж"
        )


# Ендпоінт для перевірки стану
@router.get("/health/check")
def health_check():
    """
    Перевірка стану сервісу рейсів
    """
    return {"status": "працює", "service": "flights"}