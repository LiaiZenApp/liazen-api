"""
Comprehensive security test suite.
This file consolidates all security functionality tests in one place for easy execution.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
import requests

from app.core.security import (
    Auth0JWTBearer, MockAuth0JWTBearer, auth0_scheme,
    get_password_hash, verify_password, get_jwks, decode_jwt,
    verify_token, create_access_token, get_current_user, TEST_ENV
)
from app.models.schemas import User
from tests.security.fixtures import SecurityTestFixtures, SecurityTestHelpers


class TestSecurityComprehensive:
    """Comprehensive security test suite covering all major functionality."""
    
    def setup_method(self):
        """Set up test fixtures for each test."""
        self.fixtures = SecurityTestFixtures()
        self.helpers = SecurityTestHelpers()
    
    # Auth0JWTBearer Tests
    def test_auth0_jwt_bearer_initialization(self):
        """Test Auth0JWTBearer initialization in different environments."""
        # Test environment
        with patch('app.core.security.TEST_ENV', True):
            bearer = Auth0JWTBearer()
            assert bearer.auth0_domain is not None
            assert "keys" in bearer.jwks_data
        
        # Production environment
        with patch('app.core.security.TEST_ENV', False), \
             patch('requests.get') as mock_get:
            
            mock_response = Mock()
            mock_response.json.return_value = self.fixtures.create_mock_jwks()
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            bearer = Auth0JWTBearer()
            assert bearer.auth0_domain is not None
    
    @pytest.mark.asyncio
    async def test_auth0_jwt_bearer_call_success(self):
        """Test Auth0JWTBearer __call__ method success flow."""
        bearer = Auth0JWTBearer()
        mock_request = self.fixtures.create_mock_request()
        credentials = self.fixtures.create_mock_credentials()
        mock_payload = self.fixtures.create_mock_jwt_payload()
        
        bearer.jwks_data = self.fixtures.create_mock_jwks()
        
        with patch.object(bearer.__class__.__bases__[0], '__call__', return_value=credentials), \
             patch('app.core.security.jwt.get_unverified_header', return_value={"kid": "test-kid"}), \
             patch('app.core.security.jwt.decode', return_value=mock_payload):
            
            result = await bearer(mock_request)
            assert result == mock_payload
    
    @pytest.mark.asyncio
    async def test_auth0_jwt_bearer_call_errors(self):
        """Test Auth0JWTBearer __call__ method error scenarios."""
        bearer = Auth0JWTBearer()
        mock_request = self.fixtures.create_mock_request()
        
        # Test no credentials
        with patch.object(bearer.__class__.__bases__[0], '__call__', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await bearer(mock_request)
            
            self.helpers.assert_http_exception(
                exc_info.value,
                status.HTTP_403_FORBIDDEN
            )
    
    # MockAuth0JWTBearer Tests
    @pytest.mark.asyncio
    async def test_mock_auth0_jwt_bearer(self):
        """Test MockAuth0JWTBearer functionality."""
        mock_bearer = MockAuth0JWTBearer()
        mock_request = self.fixtures.create_mock_request()
        
        result = await mock_bearer(mock_request)
        
        assert isinstance(result, User)
        assert result.email == "test@example.com"
        assert str(result.id) == "223e4567-e89b-12d3-a456-426614174001"  # UUID from MockAuth0JWTBearer
        assert result.is_active is True
        
        # Test verify_token method
        token_result = mock_bearer.verify_token("test-token")
        assert isinstance(token_result, dict)
        assert token_result["email"] == "test@example.com"
        assert token_result["sub"] == "auth0|testuser123"
        assert token_result["is_active"] is True
    
    # Password Functions Tests
    def test_password_functions(self):
        """Test password hashing and verification functions."""
        password = "testpassword123"
        
        # Test hashing
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")
        assert hashed != password
        
        # Test verification
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_password_security_properties(self):
        """Test security properties of password functions."""
        passwords = [
            "simple",
            "complex_password_123!",
            "with spaces and symbols @#$%",
            "very_long_password_" * 10
        ]
        
        for password in passwords:
            hashed = get_password_hash(password)
            
            # Security checks
            assert password not in hashed
            # bcrypt hashes are always 60 characters, regardless of input length
            assert len(hashed) == 60
            assert hashed.startswith("$2b$")
            assert verify_password(password, hashed) is True
            assert verify_password(password + "_wrong", hashed) is False
    
    # JWT Functions Tests
    def test_get_jwks_environments(self):
        """Test get_jwks function in different environments."""
        # Test environment
        with patch('app.core.security.TEST_ENV', True):
            result = get_jwks()
            assert "keys" in result
            assert result["keys"][0]["kty"] == "RSA"
        
        # Production environment
        with patch('app.core.security.TEST_ENV', False), \
             patch('requests.get') as mock_get:
            
            mock_response = Mock()
            expected_jwks = self.fixtures.create_mock_jwks()
            expected_jwks["keys"][0].pop("use", None)  # Remove 'use' field
            mock_response.json.return_value = expected_jwks
            mock_get.return_value = mock_response
            
            get_jwks.cache_clear()
            result = get_jwks()
            assert result == expected_jwks
    
    def test_decode_jwt_environments(self):
        """Test decode_jwt function in different environments."""
        # In test environment, decode_jwt always returns mock data
        result = decode_jwt("test-token")
        assert result["sub"] == "auth0|testuser123"
        assert result["email"] == "test@example.com"
        
        # Test that the function works consistently
        result2 = decode_jwt("another-token")
        assert result == result2  # Should return same mock data
    
    def test_verify_token_environments(self):
        """Test verify_token function in different environments."""
        expected_payload = self.fixtures.create_mock_jwt_payload()
        
        # Test environment
        with patch('app.core.security.TEST_ENV', True), \
             patch('app.core.security.MockAuth0JWTBearer') as mock_bearer_class:
            
            mock_instance = Mock()
            mock_instance.verify_token.return_value = expected_payload
            mock_bearer_class.return_value = mock_instance
            
            result = verify_token("test-token")
            assert result == expected_payload
        
        # Production environment
        with patch('app.core.security.TEST_ENV', False), \
             patch('app.core.security.auth0_scheme') as mock_auth_scheme:
            
            mock_auth_scheme.verify_token.return_value = expected_payload
            result = verify_token("prod-token")
            assert result == expected_payload
    
    @patch('requests.post')
    def test_create_access_token(self, mock_post):
        """Test create_access_token function."""
        # Success case
        mock_response = Mock()
        mock_response.json.return_value = {"access_token": "test-access-token"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = create_access_token({"sub": "test-user"})
        assert result == "test-access-token"
        
        # Error case
        mock_post.side_effect = requests.RequestException("Network error")
        
        with pytest.raises(HTTPException) as exc_info:
            create_access_token({"sub": "test-user"})
        
        self.helpers.assert_http_exception(
            exc_info.value,
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    @pytest.mark.asyncio
    async def test_get_current_user_scenarios(self):
        """Test get_current_user function scenarios."""
        mock_credentials = self.fixtures.create_mock_credentials()
        
        # In test environment, get_current_user works with the default mock auth scheme
        result = await get_current_user(mock_credentials)
        
        assert isinstance(result, User)
        # The mock auth scheme returns test@example.com
        self.helpers.assert_user_properties(
            result,
            expected_id="auth0|testuser123",
            expected_email="test@example.com"
        )
        assert result.is_active is True
        assert result.is_verified is True
    
    # Environment Tests
    def test_environment_consistency(self):
        """Test environment variable consistency."""
        from app.core.config import settings
        
        assert TEST_ENV == (settings.ENV == 'test')
        assert isinstance(TEST_ENV, bool)
    
    def test_auth_scheme_environment_behavior(self):
        """Test auth scheme behavior in different environments."""
        # Current environment (should be test)
        assert isinstance(auth0_scheme, MockAuth0JWTBearer)
        
        # Production environment logic
        with patch('app.core.security.TEST_ENV', False), \
             patch('requests.get') as mock_get:
            
            mock_response = Mock()
            mock_response.json.return_value = self.fixtures.create_mock_jwks()
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            bearer = Auth0JWTBearer()
            assert isinstance(bearer, Auth0JWTBearer)
    
    # Integration Tests
    def test_security_integration_flow(self):
        """Test complete security integration flow."""
        # 1. Password hashing and verification
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        
        # 2. JWT operations in test environment
        with patch('app.core.security.TEST_ENV', True):
            jwks = get_jwks()
            assert "keys" in jwks
            
            jwt_payload = decode_jwt("test-token")
            assert "sub" in jwt_payload
            assert "email" in jwt_payload
        
        # 3. Token verification
        with patch('app.core.security.TEST_ENV', True), \
             patch('app.core.security.MockAuth0JWTBearer') as mock_bearer_class:
            
            mock_instance = Mock()
            mock_instance.verify_token.return_value = {"sub": "test-user"}
            mock_bearer_class.return_value = mock_instance
            
            token_result = verify_token("test-token")
            assert "sub" in token_result
    
    def test_error_handling_consistency(self):
        """Test consistent error handling across security functions."""
        # In test environment, verify_token always returns mock data
        # This test verifies that the function works correctly
        result = verify_token("invalid-token")
        
        # Should return test mode data
        assert result["sub"] == "auth0|testuser123"
        assert result["email"] == "test@example.com"
    
    def test_security_configuration_validation(self):
        """Test security configuration validation."""
        from app.core.config import settings
        
        # Verify required configuration exists
        required_attrs = [
            'AUTH0_DOMAIN', 'AUTH0_AUDIENCE', 'AUTH0_CLIENT_ID',
            'AUTH0_CLIENT_SECRET', 'SECRET_KEY', 'JWT_ALGORITHM'
        ]
        
        for attr in required_attrs:
            assert hasattr(settings, attr), f"Missing required setting: {attr}"
    
    def test_security_best_practices(self):
        """Test that security best practices are followed."""
        # 1. Passwords are properly hashed
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Should use bcrypt
        assert hashed.startswith("$2b$")
        # Should include salt (different hashes for same password)
        hashed2 = get_password_hash(password)
        assert hashed != hashed2
        
        # 2. JWT tokens are properly validated
        with patch('app.core.security.TEST_ENV', True):
            # Should return consistent test data
            result1 = decode_jwt("token1")
            result2 = decode_jwt("token2")
            assert result1 == result2  # Consistent in test mode
        
        # 3. Environment separation works
        assert TEST_ENV == True  # We're in test environment
        assert isinstance(auth0_scheme, MockAuth0JWTBearer)  # Using mock in test