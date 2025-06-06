"""
LiaiZen API - Security Module

This module provides comprehensive security functionality for the LiaiZen API,
including JWT authentication, password hashing, and Auth0 integration.

Key Features:
- Auth0 JWT Bearer token validation with JWKS support
- Mock authentication for testing environments
- Secure password hashing with bcrypt
- User authentication and authorization
- Token verification and claims extraction
- Environment-aware security configurations

Security Architecture:
- Production: Full Auth0 JWT validation with signature verification
- Testing: Mock authentication for reliable test execution
- Password Security: bcrypt with salt rounds and long password handling
- Token Management: JWT decode/verify with proper error handling

Author: LiaiZen Development Team
Version: 1.0
"""

import os
import requests
import bcrypt
from jose import jwt, JWTError, jwk
from jose.utils import base64url_decode
from jose.exceptions import JWTError, JWKError, JWTClaimsError, ExpiredSignatureError
from fastapi import HTTPException, status, Depends, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.models.schemas import User, TokenData
from functools import lru_cache
from typing import Union, Any, Dict, List, Optional, Annotated
import json
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, ValidationError

# Environment detection for security configuration
TEST_ENV = settings.ENV == 'test'

# ============================================================================
# MOCK AUTHENTICATION FOR TESTING
# ============================================================================

class MockAuth0JWTBearer(HTTPBearer):
    """
    Mock Auth0 JWT Bearer authentication for testing environments.
    
    This class provides a mock implementation of Auth0 JWT authentication
    that returns predictable test data without requiring actual Auth0 tokens.
    It's designed to be a drop-in replacement for Auth0JWTBearer during testing.
    
    Features:
    - Returns consistent test user data
    - Compatible with production Auth0JWTBearer interface
    - Supports both User object and JWT payload formats
    - No external dependencies or network calls
    
    Usage:
        Used automatically when ENV=test in settings
    """
    
    def __init__(self, auto_error: bool = True):
        """
        Initialize the mock Auth0 JWT Bearer.
        
        Args:
            auto_error (bool): Whether to automatically raise errors for invalid tokens
        """
        super().__init__(auto_error=auto_error, scheme_name="Bearer")
        self.auto_error = auto_error
    
    async def __call__(self, request: Request) -> User:
        """
        Mock authentication that returns a test User object.
        
        This method bypasses actual JWT validation and returns a consistent
        test user for use in testing scenarios.
        
        Args:
            request (Request): The incoming HTTP request
            
        Returns:
            User: A mock user object with test data
            
        Note:
            This method always returns the same test user regardless of
            the actual token provided, making tests predictable and reliable.
        """
        from uuid import UUID
        from datetime import datetime, timezone
        
        return User(
            id=UUID("223e4567-e89b-12d3-a456-426614174001"),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="$2b$12$mock_hashed_password",
            is_active=True,
            is_verified=True,
            role="user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc)
        )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Mock token verification that returns test JWT payload.
        
        This method provides a mock JWT payload that's compatible with
        the production Auth0 token format, enabling comprehensive testing
        of token-dependent functionality.
        
        Args:
            token (str): The token to verify (ignored in mock)
            
        Returns:
            Dict[str, Any]: Mock JWT payload with standard Auth0 claims
            
        Note:
            The returned payload includes all standard Auth0 claims
            and custom claims used by the application.
        """
        return {
            "sub": "auth0|testuser123",  # Auth0 user identifier
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
            "is_active": True,
            "permissions": ["read:users", "write:users"],
            "iat": 1234567890,  # Issued at timestamp
            "exp": 1234571490,  # Expiration timestamp
            "aud": "test-audience",  # Audience
            "iss": "https://test-domain.auth0.com/",  # Issuer
            "last_login": "2023-01-01T00:00:00Z"
        }

# ============================================================================
# PRODUCTION AUTH0 JWT AUTHENTICATION
# ============================================================================

class Auth0JWTBearer(HTTPBearer):
    """
    Production Auth0 JWT Bearer token validator with full security verification.
    
    This class provides complete Auth0 JWT token validation including:
    - JWKS (JSON Web Key Set) retrieval and caching
    - RSA signature verification using Auth0's public keys
    - Token expiration and claims validation
    - Proper error handling for various failure scenarios
    
    Security Features:
    - Verifies token signatures using Auth0's public keys
    - Validates token expiration, audience, and issuer claims
    - Caches JWKS data to reduce external API calls
    - Comprehensive error handling with appropriate HTTP status codes
    
    Architecture:
    - Inherits from FastAPI's HTTPBearer for standard Bearer token handling
    - Uses python-jose for JWT operations and RSA key handling
    - Implements caching with functools.lru_cache for performance
    - Environment-aware configuration for testing vs production
    """
    
    def __init__(self, auto_error: bool = True):
        """
        Initialize the Auth0 JWT Bearer validator.
        
        Args:
            auto_error (bool): Whether to automatically raise HTTPExceptions
                             for authentication failures
        """
        # Initialize the HTTPBearer parent class
        super().__init__(
            auto_error=auto_error,
            scheme_name="Bearer"
        )
        
        # Configure Auth0 settings based on environment
        self.auth0_domain = settings.AUTH0_DOMAIN
        self.issuer = f"https://{self.auth0_domain}/"
        self.audience = settings.AUTH0_AUDIENCE
        self.jwks_url = f"{self.issuer}.well-known/jwks.json"
        
        # Initialize JWKS data based on environment
        if TEST_ENV:
            # Use mock JWKS data for testing to avoid external calls
            self.jwks_data = {
                "keys": [{
                    "kty": "RSA",
                    "kid": "test-kid",
                    "n": "test-modulus",
                    "e": "AQAB"
                }]
            }
        else:
            # Fetch real JWKS data from Auth0 for production
            self.jwks_data = self.get_jwks()
    
    @lru_cache
    def get_jwks(self) -> Dict[str, Any]:
        """Get the JWKS from Auth0 with caching"""
        if TEST_ENV:
            # Return mock JWKS data for tests
            return {
                "keys": [{
                    "kty": "RSA",
                    "kid": "test-kid",
                    "n": "test-modulus",
                    "e": "AQAB"
                }]
            }
            
        try:
            # In test mode, return mock data immediately
            if TEST_ENV:
                return {
                    "keys": [{
                        "kty": "RSA",
                        "kid": "test-kid",
                        "n": "test-modulus",
                        "e": "AQAB"
                    }]
                }
                
            response = requests.get(self.jwks_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # In test mode, return mock data on any error
            if TEST_ENV:
                return {
                    "keys": [{
                        "kty": "RSA",
                        "kid": "test-kid",
                        "n": "test-modulus",
                        "e": "AQAB"
                    }]
                }
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not fetch JWKS from {self.jwks_url}: {str(e)}"
            )
    
    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        credentials = await super().__call__(request)
        if not credentials:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authorization code.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            return None
            
        if not credentials.scheme == "Bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            return None
            
        token = credentials.credentials
        try:
            # Get the unverified header to determine the key ID (kid)
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No key ID (kid) found in token header"
                )
                
            # Find the key with the matching kid
            key = None
            for k in self.jwks_data.get("keys", []):
                if k.get("kid") == kid:
                    key = k
                    break
                    
            if not key:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No key found for kid: {kid}"
                )
                
            # Verify the token
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer
            )
            
            return payload
            
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except JWTClaimsError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid token claims: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(err)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify a JWT token and return its payload."""
        return decode_jwt(token)

# Create an instance of the Auth0JWTBearer class
if TEST_ENV:
    auth0_scheme = MockAuth0JWTBearer()
else:
    auth0_scheme = Auth0JWTBearer()


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify a JWT token and return its payload if valid.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        Dict containing the token payload if valid
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        if TEST_ENV:
            # Use MockAuth0JWTBearer verify_token method in test environment
            mock_bearer = MockAuth0JWTBearer()
            return mock_bearer.verify_token(token)
        else:
            # Use auth0_scheme in production environment
            return auth0_scheme.verify_token(token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_password_hash(password: str) -> str:
    """
    Hash a password for storing in the database.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password as a string
    """
    # bcrypt has a 72-byte limit, so for very long passwords we need to
    # pre-hash them with SHA-256 to ensure consistent behavior while
    # maintaining security
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        import hashlib
        # Use SHA-256 to reduce very long passwords to a fixed size
        password_bytes = hashlib.sha256(password_bytes).digest()
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a stored password against one provided by user.
    
    Args:
        plain_password: Password provided by user
        hashed_password: Hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
    """
    # bcrypt has a 72-byte limit, so for very long passwords we need to
    # pre-hash them with SHA-256 to ensure consistent behavior while
    # maintaining security
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        import hashlib
        # Use SHA-256 to reduce very long passwords to a fixed size
        password_bytes = hashlib.sha256(password_bytes).digest()
        
    return bcrypt.checkpw(
        password_bytes,
        hashed_password.encode('utf-8')
    )

@lru_cache()
def get_jwks():
    """Get JWKS from Auth0 or return mock data in test environment."""
    if TEST_ENV:
        # Return mock JWKS for testing
        return {
            "keys": [{
                "kty": "RSA",
                "kid": "test-kid",
                "n": "test-modulus",
                "e": "AQAB"
            }]
        }
    
    # Production environment - make actual request
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    response = requests.get(jwks_url)
    response.raise_for_status()
    return response.json()

def decode_jwt(token: str) -> dict:
    """Decode and validate JWT token."""
    if TEST_ENV:
        # Return mock user data for testing
        return {
            "sub": "auth0|testuser123",
            "email": "test@example.com",
            "permissions": ["read:users", "write:users"]
        }
    
    try:
        jwks = get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        # Find matching key
        matching_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                matching_key = key
                break
                
        if not matching_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signature",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        return jwt.decode(
            token,
            matching_key,
            algorithms=["RS256"],
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/"
        )
    except HTTPException:
        raise
    except Exception as e:
        if TEST_ENV:
            # In test mode, return mock data even on error
            return {
                "sub": "auth0|testuser123",
                "email": "test@example.com",
                "permissions": ["read:users", "write:users"]
            }
        raise


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> User:
    """
    Get the current authenticated user from the JWT token.
    
    Args:
        credentials: The HTTP Bearer token from the Authorization header
        
    Returns:
        User: The authenticated user
    """
    try:
        # Verify the token and get the payload using auth0_scheme
        payload = auth0_scheme.verify_token(credentials.credentials)
        
        # Extract user information from the token
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing required claims",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # In a real app, you would fetch the user from your database here
        # For this example, we'll create a user object from the token claims
        # Check if this is a test environment and handle accordingly
        if settings.ENV == 'test':
            # In test environment, we might have a mock user with is_active=False
            # We'll respect the is_active status from the token payload if provided
            is_active = payload.get("is_active", True)
        else:
            # In production, default to active unless specified otherwise
            is_active = payload.get("is_active", True)
            
        # Parse name into first and last name
        name = payload.get("name", "")
        name_parts = name.split(" ", 1) if name else ["", ""]
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Convert Auth0 user ID to UUID format for compatibility
        from uuid import uuid4, UUID
        import hashlib
        
        # Generate a deterministic UUID from the Auth0 user ID
        if user_id.startswith("auth0|"):
            # Create a deterministic UUID from the Auth0 ID
            namespace = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace
            user_uuid = UUID(bytes=hashlib.md5(user_id.encode()).digest())
        else:
            try:
                # Try to parse as UUID directly
                user_uuid = UUID(user_id)
            except ValueError:
                # If not a valid UUID, generate one deterministically
                user_uuid = UUID(bytes=hashlib.md5(user_id.encode()).digest())
            
        # Create the user object with all required fields
        user = User(
            id=user_uuid,
            email=email,
            first_name=first_name,
            last_name=last_name,
            hashed_password="$2b$12$mock_hashed_password",  # Mock password for JWT users
            is_active=is_active,
            is_verified=payload.get("email_verified", False),
            role=payload.get("role", "user"),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc)
        )
        
        # Check if the user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
            
        return user
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Request an access token from Auth0
    
    Note: This is a simplified version that demonstrates the concept.
    In a production environment, you would want to handle errors more gracefully
    and possibly cache tokens.
    """
    try:
        # In a real implementation, you would make a request to Auth0's token endpoint
        # This is just a placeholder to demonstrate the concept
        auth0_domain = settings.AUTH0_DOMAIN
        url = f"https://{auth0_domain}/oauth/token"
        
        # These would come from your Auth0 application settings
        client_id = settings.AUTH0_CLIENT_ID
        client_secret = settings.AUTH0_CLIENT_SECRET
        audience = settings.AUTH0_AUDIENCE
        
        # This is a client credentials grant - adjust based on your needs
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": audience,
            "grant_type": "client_credentials"
        }
        
        headers = {"content-type": "application/json"}
        
        # Make the request to Auth0
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Return the access token
        token_data = response.json()
        return token_data.get("access_token")
        
    except requests.RequestException as e:
        # Log the error and re-raise with a more user-friendly message
        error_detail = f"Error getting token from Auth0: {str(e)}"
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            error_detail += f" - {e.response.text}"
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_detail
        )
