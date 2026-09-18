"""Consistent error envelope for every /api/v1/* endpoint (docs/api/contracts.md):

    { "error": { "code": "...", "message": "...", "request_id": "..." } }
"""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.observability.middleware import get_request_id


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ApiErrorBody(BaseModel):
    error: ApiErrorDetail


class ApiException(Exception):
    """Raise from application/route code for a domain-level failure with a stable
    machine-readable `code` (as opposed to framework-level HTTP/validation errors,
    which are handled separately below)."""

    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _error_response(status_code: int, code: str, message: str, request: Request) -> JSONResponse:
    body = ApiErrorBody(error=ApiErrorDetail(code=code, message=message, request_id=get_request_id(request)))
    return JSONResponse(status_code=status_code, content=body.model_dump())


async def api_exception_handler(request: Request, exc: ApiException) -> JSONResponse:
    return _error_response(exc.status_code, exc.code, exc.message, request)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT, "VALIDATION_ERROR", str(exc.errors()), request
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(exc.status_code, "HTTP_ERROR", str(exc.detail), request)
