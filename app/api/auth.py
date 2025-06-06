"""
LiaiZen API - Authentication API Module

This module provides comprehensive authentication endpoints for the LiaiZen API,
including user login and token refresh functionality with rate limiting protection.

Key Features:
- User authentication with email/username and password
- JWT token generation and refresh
- Rate limiting to prevent brute force attacks
- Comprehensive error handling
- Integration with Auth0 and local authentication

API Endpoints:
- POST /auth/login - Authenticate user and return JWT tokens
- POST /auth/refresh - Refresh expired JWT tokens

Security Features:
- Rate limiting: 5 requests per minute per IP
- Secure password validation
- JWT token expiration handling
- Protection against brute force attacks
- Comprehensive audit logging

Architecture:
- Service layer pattern for authentication logic
- Rate limiting middleware integration
- Type-safe request/response models
- Proper HTTP status codes and error responses

Author: LiaiZen Development Team
Version: 1.0
"""

from fastapi import APIRouter, Depends, status, Request
from app.models.schemas import UserCred, TokenResponse
from app.services.auth_service import login_user, refresh_token
from app.core.rate_limiter import limiter

# ============================================================================
# ROUTER CONFIGURATION
# ============================================================================

router = APIRouter()

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def login(request: Request, user: UserCred):
    """
    Authenticate a user and return JWT access and refresh tokens.
    
    This endpoint handles user authentication using email/username and password.
    It validates credentials against the user database and returns JWT tokens
    for subsequent API access.
    
    Rate Limiting:
        - 5 requests per minute per IP address
        - Prevents brute force attacks
        - Returns 429 status code when limit exceeded
    
    Args:
        request (Request): The HTTP request object (required for rate limiting)
        user (UserCred): User credentials containing username/email and password
        
    Returns:
        TokenResponse: JWT tokens and metadata including:
            - access_token: JWT access token for API authentication
            - refresh_token: JWT refresh token for token renewal
            - expires_in: Token expiration time in seconds
            - token_type: Always "Bearer"
            - uniqueId: User's unique identifier
            
    Raises:
        HTTPException:
            - 400: Invalid credentials or inactive user
            - 401: Authentication failed
            - 429: Rate limit exceeded
            - 500: Internal server error
            
    Example:
        POST /auth/login
        {
            "username": "user@example.com",
            "password": "securepassword123"
        }
        
        Response:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "expires_in": 1800,
            "token_type": "Bearer",
            "uniqueId": "auth0|user123"
        }
        
    Security Notes:
        - Passwords are never logged or returned in responses
        - Failed login attempts are logged for security monitoring
        - Tokens have configurable expiration times
        - Rate limiting prevents automated attacks
    """
    return login_user(user)

@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("5/minute")
async def refresh(request: Request, data: TokenResponse):
    """
    Refresh JWT tokens using a valid refresh token.
    
    This endpoint allows clients to obtain new access tokens without
    requiring the user to re-authenticate. It validates the provided
    refresh token and returns new JWT tokens if valid.
    
    Rate Limiting:
        - 5 requests per minute per IP address
        - Prevents token refresh abuse
        - Returns 429 status code when limit exceeded
    
    Args:
        request (Request): The HTTP request object (required for rate limiting)
        data (TokenResponse): Token data containing the refresh token
        
    Returns:
        TokenResponse: New JWT tokens and metadata including:
            - access_token: New JWT access token
            - refresh_token: New or existing refresh token
            - expires_in: New token expiration time
            - token_type: Always "Bearer"
            - uniqueId: User's unique identifier
            
    Raises:
        HTTPException:
            - 400: Invalid or malformed refresh token
            - 401: Expired or revoked refresh token
            - 429: Rate limit exceeded
            - 500: Internal server error
            
    Example:
        POST /auth/refresh
        {
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        }
        
        Response:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "expires_in": 1800,
            "token_type": "Bearer",
            "uniqueId": "auth0|user123"
        }
        
    Security Notes:
        - Refresh tokens have longer expiration times than access tokens
        - Invalid refresh attempts are logged for security monitoring
        - Tokens can be revoked server-side if needed
        - Rate limiting prevents token refresh abuse
    """
    return refresh_token(data)
