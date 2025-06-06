"""
MockAuth0JWTBearer class tests.
Tests MockAuth0JWTBearer functionality for development environment authentication.
"""

import pytest
from unittest.mock import Mock
from app.core.security import MockAuth0JWTBearer
from app.models.schemas import User
from tests.security.fixtures import SecurityTestFixtures, SecurityTestHelpers


class TestMockAuth0JWTBearerInitialization:
    """Test MockAuth0JWTBearer initialization."""
    
    def test_init_default_auto_error(self):
        """Test initialization with default auto_error=True."""
        mock_bearer = MockAuth0JWTBearer()
        assert mock_bearer.auto_error is True
    
    def test_init_auto_error_false(self):
        """Test initialization with auto_error=False."""
        mock_bearer = MockAuth0JWTBearer(auto_error=False)
        assert mock_bearer.auto_error is False


class TestMockAuth0JWTBearerCall:
    """Test MockAuth0JWTBearer __call__ method functionality."""
    
    @pytest.mark.asyncio
    async def test_call_returns_user(self):
        """Test __call__ method returns a User object."""
        mock_bearer = MockAuth0JWTBearer()
        mock_request = SecurityTestFixtures.create_mock_request()
        
        result = await mock_bearer(mock_request)
        
        assert isinstance(result, User)
        SecurityTestHelpers.assert_user_properties(
            result,
            expected_email="test@example.com"
        )
    
    @pytest.mark.asyncio
    async def test_call_user_properties(self):
        """Test __call__ method returns User with correct properties."""
        mock_bearer = MockAuth0JWTBearer()
        mock_request = Mock()
        
        result = await mock_bearer(mock_request)
        
        assert result.email == "test@example.com"
        assert result.first_name == "Test"
        assert result.last_name == "User"
        assert result.is_active is True
        assert result.is_verified is True
        assert result.role == "user"
        assert result.hashed_password is not None
        assert result.created_at is not None
        assert result.updated_at is not None
        assert result.last_login is not None
    
    @pytest.mark.asyncio
    async def test_call_consistent_user_id(self):
        """Test __call__ method returns consistent user ID."""
        mock_bearer = MockAuth0JWTBearer()
        mock_request = Mock()
        
        result1 = await mock_bearer(mock_request)
        result2 = await mock_bearer(mock_request)
        
        # Should return the same user ID for consistency
        assert result1.id == result2.id
        assert str(result1.id) == "223e4567-e89b-12d3-a456-426614174001"


class TestMockAuth0JWTBearerIntegration:
    """Test MockAuth0JWTBearer integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_multiple_calls_same_instance(self):
        """Test multiple calls to the same instance."""
        mock_bearer = MockAuth0JWTBearer()
        mock_request = Mock()
        
        results = []
        for _ in range(3):
            result = await mock_bearer(mock_request)
            results.append(result)
        
        # All results should be User instances with same properties
        for result in results:
            assert isinstance(result, User)
            assert result.email == "test@example.com"
            assert result.is_active is True
    
    @pytest.mark.asyncio
    async def test_different_instances_same_user(self):
        """Test different instances return the same user data."""
        mock_request = Mock()
        
        bearer1 = MockAuth0JWTBearer()
        bearer2 = MockAuth0JWTBearer()
        
        result1 = await bearer1(mock_request)
        result2 = await bearer2(mock_request)
        
        # Should return equivalent user data
        assert result1.id == result2.id
        assert result1.email == result2.email
        assert result1.is_active == result2.is_active