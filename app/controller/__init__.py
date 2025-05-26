from .auth_controller import router as auth_router
from .auth_controller import get_auth_service
from .flight_controller import router as flight_router
from .crew_controller import router as crew_router
from .assignment_controller import router as assignment_router

# Список всіх роутерів для реєстрації в основному додатку
routers = [
    auth_router,
    flight_router,
    crew_router,
    assignment_router,
    get_auth_service
]

__all__ = [
    'auth_router',
    'flight_router',
    'crew_router',
    'assignment_router',
    'routers'
]