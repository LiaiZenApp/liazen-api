from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import time

from app.core.config import settings
from app.api.auth import router as auth_router

def create_test_app():
    app = FastAPI()
    
    # Create a new limiter instance for testing
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["5/minute"],
        headers_enabled=True
    )
    
    # Setup rate limiting
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please wait and try again."}
        )
    
    # Include routers with prefix
    app.include_router(auth_router, prefix="/api")
    
    return app, limiter

# Create test client and limiter
app, limiter = create_test_app()
client = TestClient(app)

def create_fresh_test_client() -> TestClient:
    """Create a fresh test client with a clean rate limiter state."""
    # Create a new app and limiter
    test_app, test_limiter = create_test_app()
    # Create a new test client
    return TestClient(test_app)
