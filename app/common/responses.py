from fastapi.responses import JSONResponse
from fastapi import Request

def custom_401_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=401, content={"detail": str(exc)})