"""
Головний файл FastAPI додатку для системи управління авіакомпанією
Точка входу для веб-сервера
"""

import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Імпорти конфігурації
from app.config.settings import get_settings
from app.config.database import init_database, close_database
from app.config.logging_config import setup_logging, get_logger, log_info, log_error

# Імпорти middleware
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.cors import setup_cors_middleware

# Імпорти контролерів
from app.controller.auth_controller import router as auth_router
from app.controller.flight_controller import router as flight_router
from app.controller.crew_controller import router as crew_router
from app.controller.assignment_controller import router as assignment_router

# Ініціалізація логування та конфігурації
settings = get_settings()
logger = get_logger(__name__)


# Lifecycle events для FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управління життєвим циклом додатку
    """
    # Startup
    log_info("Starting Airline Management System...")

    try:
        # Ініціалізація бази даних
        await init_database()
        log_info("Database connection initialized successfully")

        # Додаткові ініціалізації можна додати тут
        log_info("Application started successfully")

    except Exception as e:
        log_error(f"Failed to start application: {str(e)}")
        raise

    yield

    # Shutdown
    try:
        await close_database()
        log_info("Database connection closed")
        log_info("Application shutdown completed")
    except Exception as e:
        log_error(f"Error during shutdown: {str(e)}")


# Створення FastAPI додатку
app = FastAPI(
    title="Airline Management System",
    description="Система управління авіакомпанією з інтеграцією Keycloak",
    version="1.0.0",
    docs_url="/api/docs" if settings.is_development() else None,
    redoc_url="/api/redoc" if settings.is_development() else None,
    openapi_url="/api/openapi.json" if settings.is_development() else None,
    lifespan=lifespan
)

# Налаштування CORS
setup_cors_middleware(app)

# Додавання middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)


# Глобальний обробник помилок
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Глобальний обробник HTTP помилок
    """
    log_error(f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Глобальний обробник загальних помилок
    """
    log_error(f"Unhandled exception: {str(exc)} - {request.method} {request.url}")

    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error" if settings.is_production() else str(exc),
            "status_code": 500,
            "path": str(request.url.path)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Перевірка стану системи
    """
    return {
        "status": "healthy",
        "service": "Airline Management System",
        "version": "1.0.0",
        "environment": settings.get_environment()
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Кореневий endpoint
    """
    return {
        "message": "Airline Management System API",
        "version": "1.0.0",
        "docs": "/api/docs" if settings.is_development() else "Documentation disabled in production",
        "health": "/health"
    }


# Підключення роутерів з префіксами
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    flight_router,
    prefix="/api/v1/flights",
    tags=["Flights"]
)

app.include_router(
    crew_router,
    prefix="/api/v1/crew",
    tags=["Crew Management"]
)

app.include_router(
    assignment_router,
    prefix="/api/v1/assignments",
    tags=["Flight Assignments"]
)

# Статичні файли (для фронтенду в продакшені)
if settings.is_production():
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
        app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
    except Exception as e:
        log_error(f"Failed to mount static files: {str(e)}")


# API Info endpoint
@app.get("/api/v1/info")
async def api_info():
    """
    Інформація про API
    """
    return {
        "name": "Airline Management System API",
        "version": "1.0.0",
        "description": "REST API для системи управління авіакомпанією",
        "endpoints": {
            "auth": "/api/v1/auth",
            "flights": "/api/v1/flights",
            "crew": "/api/v1/crew",
            "assignments": "/api/v1/assignments"
        },
        "authentication": "JWT + Keycloak OAuth2",
        "database": "PostgreSQL",
        "documentation": "/api/docs" if settings.is_development() else None
    }


# Middleware для додавання security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Додавання security headers
    """
    response = await call_next(request)

    if settings.is_production():
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# Функція для запуску сервера
def run_server():
    """
    Запуск сервера з налаштуваннями
    """
    setup_logging()

    log_info(f"Starting server in {settings.get_environment()} mode")
    log_info(f"Server will be available at: http://localhost:{settings.PORT}")
    log_info(f"API documentation: http://localhost:{settings.PORT}/api/docs")

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development(),
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        loop="asyncio" if sys.platform != "win32" else "asyncio",
        workers=1 if settings.is_development() else settings.WORKERS
    )


# Додаткові utility endpoints для development
if settings.is_development():
    @app.get("/api/v1/debug/settings")
    async def debug_settings():
        """
        Debug endpoint для перегляду налаштувань (тільки для development)
        """
        return {
            "environment": settings.get_environment(),
            "database_url": settings.DATABASE_URL[:20] + "..." if settings.DATABASE_URL else None,
            "keycloak_url": settings.KEYCLOAK_SERVER_URL,
            "cors_origins": settings.CORS_ORIGINS,
            "log_level": settings.LOG_LEVEL
        }


    @app.get("/api/v1/debug/routes")
    async def debug_routes():
        """
        Debug endpoint для перегляду всіх роутів
        """
        routes = []
        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                routes.append({
                    "path": route.path,
                    "methods": list(route.methods),
                    "name": getattr(route, 'name', 'Unknown')
                })
        return {"routes": routes}

# Точка входу для запуску через python -m
if __name__ == "__main__":
    run_server()