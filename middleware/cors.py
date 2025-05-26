from typing import List

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..config.settings import get_settings


class CORSMiddleware(BaseHTTPMiddleware):
    """
    Власний CORS middleware з розширеними можливостями
    """

    def __init__(
            self,
            app,
            allow_origins: List[str] = None,
            allow_methods: List[str] = None,
            allow_headers: List[str] = None,
            allow_credentials: bool = True,
            expose_headers: List[str] = None,
            max_age: int = 600
    ):
        super().__init__(app)
        settings = get_settings()

        self.allow_origins = allow_origins or settings.cors_origins
        self.allow_methods = allow_methods or settings.cors_methods
        self.allow_headers = allow_headers or [
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
            "X-User-Agent",
            "X-Forwarded-For"
        ]
        self.allow_credentials = allow_credentials
        self.expose_headers = expose_headers or ["X-Total-Count", "X-Request-ID"]
        self.max_age = max_age

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Обробляє CORS headers для кожного запиту
        """
        origin = request.headers.get("Origin")

        # Обробка preflight запитів
        if request.method == "OPTIONS":
            return self._handle_preflight_request(request, origin)

        # Виконуємо основний запит
        response = await call_next(request)

        # Додаємо CORS headers до відповіді
        self._add_cors_headers(response, origin)

        return response

    def _handle_preflight_request(self, request: Request, origin: str) -> Response:
        """
        Обробляє preflight OPTIONS запити
        """
        response = Response(status_code=200)

        # Перевіряємо дозволений origin
        if self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin

        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"

        # Методи які дозволені
        requested_method = request.headers.get("Access-Control-Request-Method")
        if requested_method and requested_method in self.allow_methods:
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)

        # Headers які дозволені
        requested_headers = request.headers.get("Access-Control-Request-Headers")
        if requested_headers:
            # Перевіряємо кожен запитуваний header
            requested_headers_list = [h.strip() for h in requested_headers.split(",")]
            allowed_headers = [h for h in requested_headers_list if h in self.allow_headers]
            if allowed_headers:
                response.headers["Access-Control-Allow-Headers"] = ", ".join(allowed_headers)
        else:
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)

        # Максимальний час кешування preflight відповіді
        response.headers["Access-Control-Max-Age"] = str(self.max_age)

        return response

    def _add_cors_headers(self, response: Response, origin: str):
        """
        Додає CORS headers до звичайної відповіді
        """
        if self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin

        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"

        if self.expose_headers:
            response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)

    def _is_origin_allowed(self, origin: str) -> bool:
        """
        Перевіряє чи дозволений origin
        """
        if not origin:
            return False

        # Якщо дозволені всі origins
        if "*" in self.allow_origins:
            return True

        # Перевіряємо точну відповідність
        if origin in self.allow_origins:
            return True

        # Перевіряємо wildcard субдомени
        for allowed_origin in self.allow_origins:
            if allowed_origin.startswith("*."):
                domain = allowed_origin[2:]  # Видаляємо "*."
                if origin.endswith(f".{domain}") or origin == domain:
                    return True

        return False


def setup_cors_middleware(app, settings=None):
    """
    Налаштовує CORS middleware для FastAPI додатку
    """
    if not settings:
        settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=settings.cors_methods,
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
        ],
        allow_credentials=True,
        expose_headers=["X-Total-Count", "X-Request-ID"],
        max_age=600
    )