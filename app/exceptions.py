from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

class VTSException(Exception):
    """Base exception for all VTS system errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class EntityNotFoundError(VTSException):
    """Exception raised when a requested resource is not found."""
    def __init__(self, message: str):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class DuplicateEntityError(VTSException):
    """Exception raised when a unique constraint is violated."""
    def __init__(self, message: str):
        super().__init__(message, status_code=status.HTTP_400_BAD_CONTENT)


class VTSProtocolError(VTSException):
    """Exception raised when a packet violates the VTS protocol format."""
    def __init__(self, message: str):
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(VTSException)
    async def vts_exception_handler(request: Request, exc: VTSException):
        logger.error(f"VTS Custom Exception: {exc.message} on path {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "success": False}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        error_messages = []
        for err in errors:
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "Validation error")
            error_messages.append(f"[{loc}]: {msg}")
        
        detail_msg = "; ".join(error_messages)
        logger.warning(f"Validation failure: {detail_msg} on path {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": f"Validation Error: {detail_msg}", "success": False}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled general exception: {str(exc)} on path {request.url.path}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected server error occurred.", "success": False}
        )
