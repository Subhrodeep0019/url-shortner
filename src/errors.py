from typing import Any, Callable, Awaitable
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request


class ReservedAliasError(Exception):
    """User has provided a BANNED keyword as custom alias"""
    pass
class AliasTakenError(Exception):
    """The provided alias is already taken"""
    pass
class CodeGenerationError(Exception):
    """An unique short code can't be generated"""
    pass


def create_exception_handler(
        status_code: int,
        initial_details: Any
) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    async def exception_handler(req: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            content=initial_details,
            status_code=status_code
        )
    return exception_handler

def register_all_errors(app: FastAPI):
    app.add_exception_handler(
        ReservedAliasError,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_details={
                "message": "Alias is not allowed",
                "resolution": "Try a different alias",
                "error_code": "reserved_alias"
            }
        )
    )
    app.add_exception_handler(
        AliasTakenError,
        create_exception_handler(
            status_code=status.HTTP_409_CONFLICT,
            initial_details={
                "message": "Alias is already taken",
                "resolution": "Try a different alias",
                "error_code": "alias_taken"
            }
        )
    )
    app.add_exception_handler(
        CodeGenerationError,
        create_exception_handler(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            initial_details={
                "message": "Unique short code cannot be generated",
                "resolution": "Try again from start",
                "error_code": "code_generation_failed"
            }
        )
    )
