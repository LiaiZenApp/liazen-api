"""Test utilities for mocking external services."""
from unittest.mock import MagicMock
from fastapi import HTTPException

class MockAuth0JWTBearer:
    """Mock for Auth0JWTBearer to avoid real Auth0 calls during testing."""
    
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error
    
    async def __call__(self, request):
        # Return a mock token that will be validated by our test setup
        return {
            "sub": "auth0|testuser123",
            "email": "test@example.com",
            "permissions": ["read:users", "write:users"]
        }

def mock_get_jwks():
    """Mock the JWKS endpoint."""
    return {
        "keys": [
            {
                "kid": "test_kid",
                "kty": "RSA",
                "n": "test_modulus",
                "e": "AQAB"
            }
        ]
    }

def mock_decode_token(token: str):
    """Mock token decoding."""
    if token == "invalid_token":
        raise JWTError("Invalid token")
    
    return {
        "sub": "auth0|testuser123",
        "email": "test@example.com",
        "permissions": ["read:users", "write:users"]
    }
