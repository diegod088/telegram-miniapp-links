"""Custom exceptions and global FastAPI exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ── Custom Exceptions ─────────────────────────────────────────

class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str = "An error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(AppError):
    """Raised when Telegram initData verification fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)


class NotFoundError(AppError):
    """Raised when a requested resource doesn't exist."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class ForbiddenError(AppError):
    """Raised when a user lacks permission for an action."""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message=message, status_code=403)


class PlanLimitError(AppError):
    """Raised when a user exceeds their plan limits."""
    def __init__(self, message: str = "Plan limit reached", current_plan: str = "free"):
        self.current_plan = current_plan
        super().__init__(message=message, status_code=403)


class LockVerificationError(AppError):
    """Raised when lock verification fails."""
    def __init__(self, message: str = "Lock verification failed"):
        super().__init__(message=message, status_code=400)


class RateLimitError(AppError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded. Try again later."):
        super().__init__(message=message, status_code=429)


# ── Global Exception Handlers ────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        payload = {"error": exc.message}
        if isinstance(exc, PlanLimitError):
            payload["current_plan"] = exc.current_plan
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(Exception)
    async def generic_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )
