"""
LiaiZen API - Main Application Module

This module serves as the entry point for the LiaiZen FastAPI application.
It configures the FastAPI instance, middleware, routing, and application lifecycle.

Key Features:
- FastAPI application with comprehensive API documentation
- Rate limiting with SlowAPI
- CORS middleware for cross-origin requests
- JWT authentication support
- Structured logging
- Health checks and monitoring endpoints
- Modular router organization

Architecture:
- Uses dependency injection for configuration and services
- Implements proper error handling and rate limiting
- Supports both development and production environments
- Includes comprehensive API documentation with OpenAPI/Swagger

Author: LiaiZen Development Team
Version: 1.0
"""

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from jose import jwt

from app.core.rate_limiter import limiter
from app.core.config import settings
from app.api import auth, chat, events, users, members, connections, notification, profile, auth0_test
from app.core.logging_config import setup_logging, get_logger, log_request_info, log_response_info, log_error

# OpenAPI tags metadata for organizing API documentation
# These tags group related endpoints in the Swagger UI for better navigation
tags_metadata = sorted([
    {"name": "Auth", "description": "Authentication related routes - login, token refresh, user verification"},
    {"name": "Chat", "description": "Chat services - messaging between users, conversation management"},
    {"name": "Connections", "description": "Connections between users - friend requests, network building"},
    {"name": "Events", "description": "Event management - create, update, delete events and invitations"},
    {"name": "Members", "description": "Member-related operations - member profiles, relationships"},
    {"name": "Notification", "description": "Email/OTP notifications - push notifications, email alerts"},
    {"name": "Users", "description": "User registration and updates - account management, profile updates"},
    {"name": "Profiles", "description": "User profile management - detailed user information, preferences"},
    {"name": "Health", "description": "Health checks - system status, database connectivity"},
    {"name": "Root", "description": "API root - welcome message, basic information"},
], key=lambda x: x["name"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    This function handles:
    - Startup: Initialize logging, create necessary directories
    - Shutdown: Clean up resources, log shutdown message
    
    Args:
        app (FastAPI): The FastAPI application instance
        
    Yields:
        None: Control to the application during its lifetime
        
    Note:
        This replaces the deprecated @app.on_event("startup") and @app.on_event("shutdown")
        decorators in FastAPI 0.93+
    """
    # Startup operations
    logging.info("Starting LiaiZen API...")
    
    # Initialize enhanced logging configuration
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(level=log_level)
    
    # Get application logger
    app_logger = get_logger("liaizen.startup")
    app_logger.info("Enhanced logging configuration initialized")
    app_logger.info(f"Log level set to: {log_level}")
    
    # Create necessary directories for file uploads
    # These directories are used for storing user-uploaded files
    upload_dirs = [
        "uploads",
        "uploads/profile_pictures",
        "uploads/documents",
        "logs"
    ]
    
    for directory in upload_dirs:
        os.makedirs(directory, exist_ok=True)
        app_logger.debug(f"Created directory: {directory}")
    
    app_logger.info("Upload directories initialized")
    app_logger.info("LiaiZen API startup completed successfully")
    
    yield  # Application runs here
    
    # Shutdown operations
    shutdown_logger = get_logger("liaizen.shutdown")
    shutdown_logger.info("Initiating LiaiZen API shutdown...")
    # Add any cleanup operations here (close database connections, etc.)
    shutdown_logger.info("LiaiZen API shutdown completed")

# ============================================================================
# FASTAPI APPLICATION CONFIGURATION
# ============================================================================

# Create FastAPI application instance with comprehensive configuration
app = FastAPI(
    title="LiaiZen API",
    version="1.0",
    description=(
        "Professional API for iOS/Android apps with FastAPI, Auth0, PostgreSQL, and Azure-ready setup. "
        "This API provides comprehensive user management, authentication, chat services, event management, "
        "and social networking features for mobile applications."
    ),
    openapi_tags=tags_metadata,
    docs_url="/docs",  # Swagger UI documentation endpoint
    redoc_url="/redoc",  # ReDoc documentation endpoint
    lifespan=lifespan,  # Application lifecycle management
    # Additional metadata for API documentation
    contact={
        "name": "LiaiZen Development Team",
        "email": "dev@liaizen.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# Rate Limiting Configuration
# Protects the API from abuse by limiting requests per time window
app.state.limiter = limiter  # Attach limiter to app state for access in routes
app.add_middleware(SlowAPIMiddleware)  # Add rate limiting middleware
limiter.default_limits = ["100/hour"]  # Default rate limit: 100 requests per hour

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom exception handler for rate limit exceeded errors.
    
    This handler provides a consistent response format when users exceed
    the configured rate limits, helping prevent API abuse while providing
    clear feedback to legitimate users.
    
    Args:
        request (Request): The incoming HTTP request
        exc (RateLimitExceeded): The rate limit exception
        
    Returns:
        JSONResponse: Standardized error response with 429 status code
    """
    rate_limit_logger = get_logger("liaizen.rate_limit")
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    rate_limit_logger.warning(f"Rate limit exceeded for IP: {client_ip}")
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please wait and try again.",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "retry_after": "3600"  # Suggest retry after 1 hour
        }
    )

# CORS (Cross-Origin Resource Sharing) Configuration
# Enables the API to be accessed from web browsers and mobile apps
allowed_origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else ["*"]
logging.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Domains allowed to make requests
    allow_credentials=True,  # Allow cookies and authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# ============================================================================
# REQUEST/RESPONSE LOGGING MIDDLEWARE
# ============================================================================

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    Middleware for logging HTTP requests and responses.
    
    This middleware:
    - Generates unique request IDs for tracing
    - Logs incoming request details
    - Measures request processing time
    - Logs response details and performance metrics
    - Handles and logs any errors that occur
    
    Args:
        request (Request): The incoming HTTP request
        call_next: The next middleware or route handler
        
    Returns:
        Response: The HTTP response with added headers
    """
    # Generate unique request ID for tracing
    request_id = str(uuid.uuid4())[:8]
    
    # Get client IP (handle proxy headers)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    
    # Log incoming request
    start_time = time.time()
    log_request_info(
        request_id=request_id,
        method=request.method,
        path=str(request.url.path),
        client_ip=client_ip
    )
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Log response
        log_response_info(
            request_id=request_id,
            status_code=response.status_code,
            duration_ms=process_time
        )
        
        # Add request ID to response headers for debugging
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        
        return response
        
    except Exception as e:
        # Log error
        process_time = (time.time() - start_time) * 1000
        log_error(
            request_id=request_id,
            error=e,
            context=f"{request.method} {request.url.path}"
        )
        
        # Re-raise the exception to be handled by FastAPI
        raise e

# ============================================================================
# ROUTER CONFIGURATION
# ============================================================================

# Include all API routers with their respective prefixes and tags
# This modular approach allows for better organization and maintainability
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(members.router, prefix="/api/members", tags=["Members"])
app.include_router(connections.router, prefix="/api/connections", tags=["Connections"])
app.include_router(notification.router, prefix="/api/notification", tags=["Notification"])
app.include_router(profile.router, prefix="/api/profiles", tags=["Profiles"])
app.include_router(auth0_test.router, prefix="/api/auth0-test", tags=["Auth0 Test"])

# ============================================================================
# AUTHENTICATION CONFIGURATION
# ============================================================================

# HTTP Bearer token scheme for JWT authentication
auth_scheme = HTTPBearer()

def decode_jwt(token: str) -> dict:
    """
    Simple JWT decode function for development and testing purposes.
    
    WARNING: This function uses get_unverified_claims() which does NOT verify
    the token signature. In production, you should use proper JWT verification
    with Auth0's public keys or your own secret key.
    
    Args:
        token (str): The JWT token to decode
        
    Returns:
        dict: The decoded JWT payload/claims
        
    Raises:
        HTTPException: If the token is invalid or cannot be decoded
        
    Note:
        For production use, replace this with proper JWT verification:
        - Verify token signature using Auth0 public keys
        - Check token expiration
        - Validate issuer and audience claims
        - Handle token refresh logic
    """
    try:
        # SECURITY WARNING: This does not verify the token signature!
        # Only use for development/testing purposes
        payload = jwt.get_unverified_claims(token)
        auth_logger = get_logger("liaizen.auth")
        auth_logger.debug(f"Decoded JWT payload: {payload}")
        return payload
    except Exception as e:
        auth_logger = get_logger("liaizen.auth")
        auth_logger.warning(f"JWT decode failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

@app.get("/api/me", tags=["Auth"])
async def get_current_user(token: str = Depends(auth_scheme)):
    """
    Get current user information from JWT token.
    
    This endpoint extracts user information from the provided JWT token.
    It's primarily used for testing authentication and getting user context.
    
    Args:
        token (str): JWT token from Authorization header
        
    Returns:
        dict: User information from JWT claims
        
    Raises:
        HTTPException: If token is invalid or missing
        
    Example:
        GET /api/me
        Authorization: Bearer <jwt_token>
        
        Response:
        {
            "sub": "auth0|user_id",
            "email": "user@example.com",
            "name": "User Name",
            ...
        }
    """
    return decode_jwt(token)

# ============================================================================
# CORE API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
def read_root():
    """
    API root endpoint providing welcome message and basic information.
    
    This endpoint serves as the entry point for the API, providing
    basic information about the service and confirming it's running.
    
    Returns:
        dict: Welcome message and API information
        
    Example:
        GET /
        
        Response:
        {
            "message": "Welcome to LiaiZen API",
            "version": "1.0",
            "docs": "/docs",
            "status": "operational"
        }
    """
    return {
        "message": "Welcome to LiaiZen API",
        "version": "1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "operational"
    }

@app.get("/health", tags=["Health"])
def health():
    """
    Health check endpoint for monitoring and load balancers.
    
    This endpoint is used by:
    - Docker health checks
    - Kubernetes liveness/readiness probes
    - Load balancers for health monitoring
    - Monitoring systems for uptime checks
    
    Returns:
        dict: Simple status indicator
        
    Example:
        GET /health
        
        Response:
        {
            "status": "ok",
            "timestamp": "2023-12-01T12:00:00Z"
        }
    """
    from datetime import datetime
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "LiaiZen API"
    }

