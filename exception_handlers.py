from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

#custom validation exception
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_msg = [err["msg"] for err in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"errors": error_msg}
    )

#custom http exception
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
