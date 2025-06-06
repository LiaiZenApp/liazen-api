"""
Auth0JWTBearer class tests.
Tests Auth0JWTBearer functionality for JWT token validation and authentication.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
import requests

from app.core.security import Auth0JWTBearer
from tests.security.fixtures import SecurityTestFixtures


class TestAuth0JWTBearerInitialization:
    """Test Auth0JWTBearer initialization in different environments."""
    
    def test_init_test_environment(self):
        """Test initialization in test environment."""
        with patch('app.core.security.TEST_ENV', True):
            bearer = Auth0JWTBearer()
            
            assert bearer.auth0_domain is not None
            assert bearer.issuer.startswith("https://")
            assert bearer.audience is not None
            assert bearer.jwks_url.endswith("/.well-known/jwks.json")
            assert "keys" in bearer.jwks_data
    
    def test_init_production_environment(self):
        """Test initialization in production environment."""
        with patch('app.core.security.TEST_ENV', False), \
             patch('requests.get') as mock_get:
            
            mock_response = Mock()
            mock_response.json.return_value = SecurityTestFixtures.create_mock_jwks()
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            bearer = Auth0JWTBearer()
            
            assert bearer.auth0_domain is not None
            assert bearer.issuer.startswith("https://")
            assert bearer.audience is not None
            assert bearer.jwks_url.endswith("/.well-known/jwks.json")


class TestAuth0JWTBearerGetJwks:
    """Test get_jwks method functionality."""
    
    def test_get_jwks_test_environment(self):
        """Test get_jwks in test environment."""
        with patch('app.core.security.TEST_ENV', True):
            bearer = Auth0JWTBearer()
            result = bearer.get_jwks()
            
            assert "keys" in result
            assert len(result["keys"]) > 0
            assert result["keys"][0]["kty"] == "RSA"
    
    @patch('requests.get')
    def test_get_jwks_production_success(self, mock_get):
        """Test get_jwks in production with successful request."""
        mock_jwks = SecurityTestFixtures.create_mock_jwks()
        mock_response = Mock()
        mock_response.json.return_value = mock_jwks
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch('app.core.security.TEST_ENV', False):
            bearer = Auth0JWTBearer()
            result = bearer.get_jwks()
            
            assert result == mock_jwks
            mock_get.assert_called()
    
    @patch('requests.get')
    def test_get_jwks_production_failure(self, mock_get):
        """Test get_jwks in production with failed request."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        with patch('app.core.security.TEST_ENV', False):
            with pytest.raises(HTTPException) as exc_info:
                Auth0JWTBearer()
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Could not fetch JWKS" in str(exc_info.value.detail)


class TestAuth0JWTBearerCall:
    """Test Auth0JWTBearer __call__ method functionality."""
    
    @pytest.mark.asyncio
    async def test_call_no_credentials(self):
        """Test __call__ with no credentials."""
        bearer = Auth0JWTBearer()
        mock_request = SecurityTestFixtures.create_mock_request()
        
        with patch.object(bearer.__class__.__bases__[0], '__call__', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await bearer(mock_request)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_call_invalid_scheme(self):
        """Test __call__ with invalid authentication scheme."""
        bearer = Auth0JWTBearer()
        mock_request = SecurityTestFixtures.create_mock_request()
        invalid_credentials = HTTPAuthorizationCredentials(scheme="Basic", credentials="test")
        
        with patch.object(bearer.__class__.__bases__[0], '__call__', return_value=invalid_credentials):
            with pytest.raises(HTTPException) as exc_info:
                await bearer(mock_request)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_call_success(self):
        """Test __call__ with successful token validation."""
        bearer = Auth0JWTBearer()
        mock_request = SecurityTestFixtures.create_mock_request()
        credentials = SecurityTestFixtures.create_mock_credentials()
        mock_payload = SecurityTestFixtures.create_mock_jwt_payload()
        
        bearer.jwks_data = SecurityTestFixtures.create_mock_jwks()
        
        with patch.object(bearer.__class__.__bases__[0], '__call__', return_value=credentials), \
             patch('app.core.security.jwt.get_unverified_header', return_value={"kid": "test-kid"}), \
             patch('app.core.security.jwt.decode', return_value=mock_payload):
            
            result = await bearer(mock_request)
            
            assert result == mock_payload
    
    @pytest.mark.asyncio
    async def test_call_expired_token(self):
        """Test __call__ with expired token."""
        bearer = Auth0JWTBearer()
        mock_request = SecurityTestFixtures.create_mock_request()
        credentials = SecurityTestFixtures.create_mock_credentials()
        
        bearer.jwks_data = SecurityTestFixtures.create_mock_jwks()
        
        with patch.object(bearer.__class__.__bases__[0], '__call__', return_value=credentials), \
             patch('app.core.security.jwt.get_unverified_header', return_value={"kid": "test-kid"}), \
             patch('app.core.security.jwt.decode', side_effect=ExpiredSignatureError("Token expired")):
            
            with pytest.raises(HTTPException) as exc_info:
                await bearer(mock_request)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Token has expired" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_call_jwt_claims_error(self):
        """Test __call__ with JWT claims error."""
        bearer = Auth0JWTBearer()
        mock_request = SecurityTestFixtures.create_mock_request()
        credentials = SecurityTestFixtures.create_mock_credentials()
        
        bearer.jwks_data = SecurityTestFixtures.create_mock_jwks()
        
        with patch.object(bearer.__class__.__bases__[0], '__call__', return_value=credentials), \
             patch('app.core.security.jwt.get_unverified_header', return_value={"kid": "test-kid"}), \
             patch('app.core.security.jwt.decode', side_effect=JWTClaimsError("Invalid claims")):
            
            with pytest.raises(HTTPException) as exc_info:
                await bearer(mock_request)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Invalid token claims" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_call_jwt_error(self):
        """Test __call__ with JWT error."""
        bearer = Auth0JWTBearer()
        mock_request = SecurityTestFixtures.create_mock_request()
        credentials = SecurityTestFixtures.create_mock_credentials()
        
        bearer.jwks_data = SecurityTestFixtures.create_mock_jwks()
        
        with patch.object(bearer.__class__.__bases__[0], '__call__', return_value=credentials), \
             patch('app.core.security.jwt.get_unverified_header', return_value={"kid": "test-kid"}), \
             patch('app.core.security.jwt.decode', side_effect=JWTError("Invalid token")):
            
            with pytest.raises(HTTPException) as exc_info:
                await bearer(mock_request)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Invalid token" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_call_general_exception(self):
        """Test __call__ with general exception."""
        bearer = Auth0JWTBearer()
        mock_request = SecurityTestFixtures.create_mock_request()
        credentials = SecurityTestFixtures.create_mock_credentials()
        
        with patch.object(bearer.__class__.__bases__[0], '__call__', return_value=credentials), \
             patch('app.core.security.jwt.get_unverified_header', side_effect=Exception("Unexpected error")):
            
            with pytest.raises(HTTPException) as exc_info:
                await bearer(mock_request)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Could not validate credentials" in str(exc_info.value.detail)


class TestAuth0JWTBearerAutoError:
    """Test Auth0JWTBearer auto_error functionality."""
    
    @pytest.mark.asyncio
    async def test_auto_error_false_no_credentials(self):
        """Test auto_error=False with no credentials."""
        bearer = Auth0JWTBearer(auto_error=False)
        mock_request = SecurityTestFixtures.create_mock_request()
        
        with patch.object(bearer.__class__.__bases__[0], '__call__', return_value=None):
            result = await bearer(mock_request)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_auto_error_false_invalid_scheme(self):
        """Test auto_error=False with invalid scheme."""
        bearer = Auth0JWTBearer(auto_error=False)
        mock_request = SecurityTestFixtures.create_mock_request()
        invalid_credentials = HTTPAuthorizationCredentials(scheme="Basic", credentials="test")
        
        with patch.object(bearer.__class__.__bases__[0], '__call__', return_value=invalid_credentials):
            result = await bearer(mock_request)
            assert result is None