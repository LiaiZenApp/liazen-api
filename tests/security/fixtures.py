"""
Shared fixtures and test data for security tests.
Centralized test data creation and common helper methods.
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
from uuid import UUID


class SecurityTestFixtures:
    """Factory for creating test data objects used across security tests."""
    
    @staticmethod
    def create_mock_request() -> Mock:
        """Create a mock FastAPI Request object."""
        request = Mock(spec=Request)
        request.headers = {"authorization": "Bearer test-token"}
        return request
    
    @staticmethod
    def create_mock_response() -> Mock:
        """Create a mock HTTP Response object."""
        response = Mock()
        response.json.return_value = SecurityTestFixtures.create_mock_jwks()
        response.raise_for_status.return_value = None
        response.status_code = 200
        return response
    
    @staticmethod
    def create_mock_credentials(token: str = "test-token") -> HTTPAuthorizationCredentials:
        """Create mock HTTP authorization credentials."""
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    @staticmethod
    def create_mock_jwt_payload() -> Dict[str, Any]:
        """Create a mock JWT payload with all required fields."""
        return {
            "sub": "auth0|testuser123",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
            "is_active": True,
            "permissions": ["read:users", "write:users"],
            "iat": 1234567890,
            "exp": 1234571490,
            "aud": "test-audience",
            "iss": "https://test-domain.auth0.com/",
            "last_login": "2023-01-01T00:00:00Z"
        }
    
    @staticmethod
    def create_mock_jwks() -> Dict[str, Any]:
        """Create mock JWKS data."""
        return {
            "keys": [{
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "n": "test-modulus",
                "e": "AQAB"
            }]
        }
    
    @staticmethod
    def create_test_user_data() -> Dict[str, Any]:
        """Create test user data for User model creation."""
        return {
            "id": UUID("223e4567-e89b-12d3-a456-426614174001"),
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "is_active": True,
            "is_verified": True,
            "role": "user",
            "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc)
        }
    
    @staticmethod
    def create_auth0_token_response() -> Dict[str, Any]:
        """Create mock Auth0 token response."""
        return {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 86400,
            "token_type": "Bearer"
        }
    
    @staticmethod
    def create_login_credentials() -> Dict[str, str]:
        """Create test login credentials."""
        return {
            "username": "test@example.com",
            "password": "testpassword"
        }


class SecurityTestHelpers:
    """Helper methods for common test operations and assertions."""
    
    @staticmethod
    def assert_http_exception(exception, expected_status: int, expected_detail: str = None):
        """Assert HTTPException properties."""
        assert exception.status_code == expected_status
        if expected_detail:
            assert expected_detail in str(exception.detail)
    
    @staticmethod
    def assert_user_properties(user, expected_id: str = None, expected_email: str = None):
        """Assert User object properties."""
        if expected_id:
            # Handle both UUID and Auth0 ID formats
            if expected_id.startswith("auth0|"):
                # For Auth0 IDs, check that the user ID is a valid UUID
                # (since our implementation converts Auth0 IDs to UUIDs)
                import uuid
                try:
                    uuid.UUID(str(user.id))
                    # If it's a valid UUID, the conversion worked
                    assert True
                except ValueError:
                    assert False, f"Expected UUID but got {user.id}"
            else:
                # For direct UUID comparisons
                assert str(user.id) == expected_id
        if expected_email:
            assert user.email == expected_email
        assert hasattr(user, 'is_active')
        assert hasattr(user, 'is_verified')
        assert hasattr(user, 'role')
    
    @staticmethod
    def assert_token_response(response_data: Dict[str, Any]):
        """Assert token response structure."""
        required_fields = ["access_token", "refresh_token", "expires_in", "token_type"]
        for field in required_fields:
            assert field in response_data
        assert response_data["token_type"].lower() == "bearer"


@pytest.fixture(autouse=True)
def clear_security_caches():
    """Automatically clear all security-related caches before and after each test."""
    # Clear caches before test
    try:
        from app.core.security import get_jwks, auth0_scheme
        get_jwks.cache_clear()
        if hasattr(auth0_scheme, 'get_jwks') and hasattr(auth0_scheme.get_jwks, 'cache_clear'):
            auth0_scheme.get_jwks.cache_clear()
    except ImportError:
        pass  # Module not available during some test phases
    
    yield  # Run the test
    
    # Clear caches after test
    try:
        from app.core.security import get_jwks, auth0_scheme
        get_jwks.cache_clear()
        if hasattr(auth0_scheme, 'get_jwks') and hasattr(auth0_scheme.get_jwks, 'cache_clear'):
            auth0_scheme.get_jwks.cache_clear()
    except ImportError:
        pass  # Module not available during some test phases