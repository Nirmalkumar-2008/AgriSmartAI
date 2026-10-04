"""
AgriSmartAI - Custom Middleware & Exception Handling
Handles validation errors and global server exceptions with human-readable JSON formats.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats Pydantic 422 validation errors into clear human-readable error messages."""
    errors = []
    for error in exc.errors():
        field = " -> ".join([str(loc) for loc in error["loc"]])
        msg = error["msg"]
        errors.append(f"Field '{field}': {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error_type": "Validation Error",
            "message": "Invalid input parameters provided.",
            "details": errors
        }
    )
