"""
Dependencies tests.
Tests dependency injection functionality for user authentication and authorization.
"""

import pytest
from datetime import datetime, timezone
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from uuid import uuid4
from jose import JWTError

from app.api.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    oauth2_scheme
)
from app.models.schemas import User
from app.main import app
from tests.security.fixtures import SecurityTestFixtures, SecurityTestHelpers


class TestUserFactory:
    """Factory for creating test users with specified properties."""
    
    @staticmethod
    def create_test_user(
        user_id=None,
        email="test@example.com",
        is_active=True,
        is_verified=True,
        role="user"
    ):
        """Create a test user with specified properties."""
        from uuid import UUID
        if user_id and isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                user_id = uuid4()
        elif not user_id:
            user_id = uuid4()
            
        return User(
            id=user_id,
            email=email,
            first_name="Test",
            last_name="User",
            is_active=is_active,
            is_verified=is_verified,
            role=role,
            hashed_password="hashed_password_placeholder",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc)
        )


class TestGetCurrentUser:
    """Test get_current_user dependency."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test get_current_user with valid token."""
        test_user_id = str(uuid4())
        test_email = "test@example.com"
        
        mock_jwt_payload = {
            "sub": test_user_id,
            "email": test_email,
            "exp": 9999999999,  # Far future expiration
            "iss": "https://your-issuer-url/",
            "aud": "your-audience"
        }
        
        expected_user = TestUserFactory.create_test_user(
            user_id=test_user_id,
            email=test_email
        )
        
        with patch("app.api.dependencies.jwt.decode", return_value=mock_jwt_payload), \
             patch("app.api.dependencies.settings") as mock_settings, \
             patch("app.api.dependencies.User", return_value=expected_user):
            
            mock_settings.SECRET_KEY = "test-secret-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            
            result = await get_current_user(token="valid_token")
            
            SecurityTestHelpers.assert_user_properties(
                result,
                expected_id=test_user_id,
                expected_email=test_email
            )
            assert result.is_active is True
            assert result.role == "user"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid token."""
        with patch("app.api.dependencies.jwt.decode", side_effect=JWTError("Invalid token")), \
             patch("app.api.dependencies.settings") as mock_settings:
            
            mock_settings.SECRET_KEY = "test-secret-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token="invalid_token")
            
            SecurityTestHelpers.assert_http_exception(
                exc_info.value,
                status.HTTP_401_UNAUTHORIZED,
                "Could not validate credentials"
            )
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token_in_test_env(self):
        """Test get_current_user with no token in test environment."""
        with patch("app.api.dependencies.settings") as mock_settings:
            mock_settings.ENV = "test"
            mock_settings.SECRET_KEY = "test-secret-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            
            result = await get_current_user(token=None)
            
            assert result is not None
            assert result.email == "test@example.com"
            assert result.is_active is True
            SecurityTestHelpers.assert_user_properties(result)
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token_in_production(self):
        """Test get_current_user with no token in production environment."""
        with patch("app.api.dependencies.settings") as mock_settings:
            mock_settings.ENVIRONMENT = "production"
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=None)
            
            SecurityTestHelpers.assert_http_exception(
                exc_info.value,
                status.HTTP_401_UNAUTHORIZED
            )
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self):
        """Test get_current_user with expired token."""
        with patch("app.api.dependencies.jwt.decode", side_effect=JWTError("Token expired")), \
             patch("app.api.dependencies.settings") as mock_settings:
            
            mock_settings.SECRET_KEY = "test-secret-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token="expired_token")
            
            SecurityTestHelpers.assert_http_exception(
                exc_info.value,
                status.HTTP_401_UNAUTHORIZED,
                "Could not validate credentials"
            )


class TestGetCurrentActiveUser:
    """Test get_current_active_user dependency."""
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_success(self):
        """Test get_current_active_user with active user."""
        active_user = TestUserFactory.create_test_user(is_active=True)
        
        result = await get_current_active_user(current_user=active_user)
        
        assert result == active_user
        assert result.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self):
        """Test get_current_active_user with inactive user."""
        inactive_user = TestUserFactory.create_test_user(
            is_active=False,
            email="inactive@example.com"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=inactive_user)
        
        SecurityTestHelpers.assert_http_exception(
            exc_info.value,
            status.HTTP_400_BAD_REQUEST,
            "Inactive user"
        )


class TestGetCurrentAdminUser:
    """Test get_current_admin_user dependency."""
    
    @pytest.mark.asyncio
    async def test_get_current_admin_user_success(self):
        """Test get_current_admin_user with admin user."""
        admin_user = TestUserFactory.create_test_user(
            role="admin",
            email="admin@example.com"
        )
        
        result = await get_current_admin_user(current_user=admin_user)
        
        assert result == admin_user
        assert result.role == "admin"
    
    @pytest.mark.asyncio
    async def test_get_current_admin_user_unauthorized(self):
        """Test get_current_admin_user with non-admin user."""
        regular_user = TestUserFactory.create_test_user(
            role="user",
            email="user@example.com"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(current_user=regular_user)
        
        SecurityTestHelpers.assert_http_exception(
            exc_info.value,
            status.HTTP_403_FORBIDDEN,
            "The user doesn't have enough privileges"
        )
    
    @pytest.mark.asyncio
    async def test_get_current_admin_user_inactive_admin(self):
        """Test get_current_admin_user with inactive admin user."""
        inactive_admin = TestUserFactory.create_test_user(
            role="admin",
            email="inactive_admin@example.com",
            is_active=False
        )
        
        # Test the dependency chain directly
        # get_current_admin_user depends on get_current_active_user
        # get_current_active_user should raise HTTPException for inactive users
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=inactive_admin)
        
        SecurityTestHelpers.assert_http_exception(
            exc_info.value,
            status.HTTP_400_BAD_REQUEST,
            "Inactive user"
        )
        
        # To properly test get_current_admin_user, we need to first call
        # get_current_active_user which will raise the exception
        # Since get_current_admin_user depends on get_current_active_user,
        # the inactive user will be caught by get_current_active_user first
        try:
            active_user = await get_current_active_user(current_user=inactive_admin)
            # This should not be reached
            await get_current_admin_user(current_user=active_user)
            assert False, "Should have raised HTTPException for inactive user"
        except HTTPException as exc:
            SecurityTestHelpers.assert_http_exception(
                exc,
                status.HTTP_400_BAD_REQUEST,
                "Inactive user"
            )


class TestOAuth2Scheme:
    """Test OAuth2 scheme functionality."""
    
    def test_oauth2_scheme_exists(self):
        """Test that oauth2_scheme is properly configured."""
        assert oauth2_scheme is not None
        assert hasattr(oauth2_scheme, 'tokenUrl')
        assert oauth2_scheme.tokenUrl == "/auth/login"


class TestDependenciesIntegration:
    """Test dependencies integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_user_role_hierarchy(self):
        """Test user role hierarchy in dependencies."""
        # Test regular user
        regular_user = TestUserFactory.create_test_user(role="user")
        
        # Should pass active user check
        active_result = await get_current_active_user(current_user=regular_user)
        assert active_result == regular_user
        
        # Should fail admin check
        with pytest.raises(HTTPException):
            await get_current_admin_user(current_user=regular_user)
        
        # Test admin user
        admin_user = TestUserFactory.create_test_user(role="admin")
        
        # Should pass both checks
        active_admin = await get_current_active_user(current_user=admin_user)
        assert active_admin == admin_user
        
        admin_result = await get_current_admin_user(current_user=admin_user)
        assert admin_result == admin_user
    
    @pytest.mark.asyncio
    async def test_inactive_user_scenarios(self):
        """Test various inactive user scenarios."""
        inactive_scenarios = [
            {"role": "user", "expected_error": "Inactive user"},
            {"role": "admin", "expected_error": "Inactive user"},
            {"role": "moderator", "expected_error": "Inactive user"}
        ]
        
        for scenario in inactive_scenarios:
            inactive_user = TestUserFactory.create_test_user(
                role=scenario["role"],
                is_active=False
            )
            
            # All inactive users should fail active user check
            with pytest.raises(HTTPException) as exc_info:
                await get_current_active_user(current_user=inactive_user)
            
            SecurityTestHelpers.assert_http_exception(
                exc_info.value,
                status.HTTP_400_BAD_REQUEST,
                scenario["expected_error"]
            )
    
    @pytest.mark.asyncio
    async def test_user_verification_status(self):
        """Test user verification status handling."""
        # Test verified user
        verified_user = TestUserFactory.create_test_user(is_verified=True)
        result = await get_current_active_user(current_user=verified_user)
        assert result.is_verified is True
        
        # Test unverified user (should still pass if active)
        unverified_user = TestUserFactory.create_test_user(is_verified=False)
        result = await get_current_active_user(current_user=unverified_user)
        assert result.is_verified is False
        assert result.is_active is True  # Still active