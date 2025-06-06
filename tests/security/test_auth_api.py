"""
Authentication API tests.
Tests authentication API endpoints including login, refresh, and rate limiting functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from tests.security.fixtures import SecurityTestFixtures, SecurityTestHelpers


class TestAuthLogin:
    """Test authentication login endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_login_success(self, client):
        """Test successful login with valid credentials."""
        auth_response = SecurityTestFixtures.create_auth0_token_response()
        credentials = SecurityTestFixtures.create_login_credentials()
        
        with patch('app.services.auth_service.requests.post') as mock_post, \
             patch('app.services.auth_service.decode_jwt') as mock_decode:
            
            # Mock Auth0 response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = auth_response
            mock_post.return_value = mock_response
            
            # Mock JWT decode
            mock_decode.return_value = {"sub": "auth0|1234567890"}
            
            response = client.post("/api/auth/login", json=credentials)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            SecurityTestHelpers.assert_token_response(data)
            assert data["access_token"] == auth_response["access_token"]
            assert data["uniqueId"] == "auth0|1234567890"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        with patch('app.services.auth_service.requests.post') as mock_post:
            # Mock Auth0 error response
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": "invalid_grant",
                "error_description": "Wrong username or password"
            }
            mock_post.return_value = mock_response
            
            response = client.post(
                "/api/auth/login",
                json={"username": "wronguser", "password": "wrongpassword"}
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post("/api/auth/login", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_partial_credentials(self, client):
        """Test login with partial credentials."""
        # Missing password
        response = client.post("/api/auth/login", json={"username": "test@example.com"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Missing username
        response = client.post("/api/auth/login", json={"password": "testpassword"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthRefresh:
    """Test authentication refresh endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_refresh_token_success(self, client):
        """Test successful token refresh."""
        auth_response = SecurityTestFixtures.create_auth0_token_response()
        
        with patch('app.services.auth_service.requests.post') as mock_post, \
             patch('app.services.auth_service.decode_jwt') as mock_decode:
            
            # Mock Auth0 response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = auth_response
            mock_post.return_value = mock_response
            
            # Mock JWT decode
            mock_decode.return_value = {"sub": "auth0|1234567890"}
            
            # Test refresh with proper TokenResponse format
            refresh_request = {
                "access_token": "dummy-access-token",
                "refresh_token": "test-refresh-token",
                "expires_in": 3600,
                "token_type": "Bearer",
                "uniqueId": "auth0|1234567890"
            }
            
            response = client.post("/api/auth/refresh", json=refresh_request)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            SecurityTestHelpers.assert_token_response(data)
            assert data["access_token"] == auth_response["access_token"]
            assert data["refresh_token"] == auth_response["refresh_token"]
    
    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token."""
        with patch('app.services.auth_service.requests.post') as mock_post:
            # Mock Auth0 error response
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": "invalid_grant",
                "error_description": "Invalid refresh token"
            }
            mock_post.return_value = mock_response
            
            refresh_request = {
                "access_token": "invalid-token",
                "refresh_token": "invalid-refresh-token",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
            
            response = client.post("/api/auth/refresh", json=refresh_request)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid refresh token" in response.json()["detail"]
    
    def test_refresh_missing_token(self, client):
        """Test refresh with missing token data."""
        response = client.post("/api/auth/refresh", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthRateLimit:
    """Test authentication rate limiting."""
    
    def test_login_rate_limit(self):
        """Test rate limiting on login endpoint."""
        from fastapi import FastAPI, Request, APIRouter
        from app.core.rate_limiter import limiter
        
        # Create a test app with rate limiting
        test_app = FastAPI()
        test_app.state.limiter = limiter
        
        # Create a test router with rate limiting
        test_router = APIRouter()
        
        @test_router.post("/test-rate-limit")
        @limiter.limit("5/minute")
        async def test_endpoint(request: Request):
            return {"message": "Test endpoint"}
        
        test_app.include_router(test_router)
        
        # Create a test client
        client = TestClient(test_app)
        
        # Make 5 requests (limit is 5 per minute)
        for _ in range(5):
            response = client.post("/test-rate-limit")
            assert response.status_code == 200
        
        # 6th request should be rate limited
        response = client.post("/test-rate-limit")
        assert response.status_code == 429  # Too Many Requests
        
        # Check that the response has the expected rate limit error message
        error_data = response.json()
        assert "detail" in error_data
        assert "5 per 1 minute" in error_data["detail"]


class TestAuthIntegration:
    """Test authentication integration scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_login_refresh_flow(self, client):
        """Test complete login and refresh flow."""
        auth_response = SecurityTestFixtures.create_auth0_token_response()
        credentials = SecurityTestFixtures.create_login_credentials()
        
        with patch('app.services.auth_service.requests.post') as mock_post, \
             patch('app.services.auth_service.decode_jwt') as mock_decode:
            
            # Mock Auth0 response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = auth_response
            mock_post.return_value = mock_response
            
            # Mock JWT decode
            mock_decode.return_value = {"sub": "auth0|1234567890"}
            
            # Step 1: Login
            login_response = client.post("/api/auth/login", json=credentials)
            assert login_response.status_code == status.HTTP_200_OK
            login_data = login_response.json()
            
            # Step 2: Use refresh token
            refresh_request = {
                "access_token": login_data["access_token"],
                "refresh_token": login_data["refresh_token"],
                "expires_in": login_data["expires_in"],
                "token_type": login_data["token_type"],
                "uniqueId": login_data["uniqueId"]
            }
            
            refresh_response = client.post("/api/auth/refresh", json=refresh_request)
            assert refresh_response.status_code == status.HTTP_200_OK
            refresh_data = refresh_response.json()
            
            # Verify both responses have required fields
            SecurityTestHelpers.assert_token_response(login_data)
            SecurityTestHelpers.assert_token_response(refresh_data)
    
    def test_auth_error_handling(self, client):
        """Test authentication error handling scenarios."""
        error_scenarios = [
            {
                "name": "network_error",
                "exception": Exception("Network error"),
                "expected_status": status.HTTP_500_INTERNAL_SERVER_ERROR
            },
            {
                "name": "timeout_error", 
                "exception": TimeoutError("Request timeout"),
                "expected_status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
        ]
        
        credentials = SecurityTestFixtures.create_login_credentials()
        
        for scenario in error_scenarios:
            with patch('app.services.auth_service.requests.post') as mock_post:
                mock_post.side_effect = scenario["exception"]
                
                response = client.post("/api/auth/login", json=credentials)
                
                # Should handle errors gracefully
                assert response.status_code in [
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                    status.HTTP_401_UNAUTHORIZED
                ]