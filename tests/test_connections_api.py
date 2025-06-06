"""
Test cases for Connections API endpoints.

This module contains comprehensive tests for all connection-related API endpoints.
"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi import status, Depends, HTTPException, Request
from app.core.security import get_current_user
from fastapi.testclient import TestClient
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.main import app
from app.models.schemas import User, ConnectionCreate, ConnectionStatus, ConnectionDTO
from app.api.connections import get_connection_service

# Test Constants - Single source of truth
class TestConstants:
    TEST_USER_ID = "123e4567-e89b-12d3-a456-426614174000"
    TARGET_USER_ID = "223e4567-e89b-12d3-a456-426614174001"
    OTHER_USER_ID = "423e4567-e89b-12d3-a456-426614174003"
    CONNECTION_ID = "323e4567-e89b-12d3-a456-426614174002"
    INACTIVE_USER_ID = "523e4567-e89b-12d3-a456-426614174004"

# Test Data Factory
class TestDataFactory:
    """Factory for creating test data objects."""
    
    @staticmethod
    def create_user(
        user_id: str = TestConstants.TEST_USER_ID,
        email: str = "test@example.com",
        first_name: str = "Test",
        last_name: str = "User",
        is_active: bool = True,
        is_verified: bool = True,
        role: str = "user",
        **kwargs
    ) -> User:
        """Create a test user with the given parameters."""
        return User(
            id=UUID(user_id) if isinstance(user_id, str) else user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            is_verified=is_verified,
            role=role,
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
            **kwargs
        )
    
    @staticmethod
    def create_connection(
        connection_id: str = TestConstants.CONNECTION_ID,
        user_id: str = TestConstants.TEST_USER_ID,
        target_user_id: str = TestConstants.TARGET_USER_ID,
        connection_status: str = "pending",
        **kwargs
    ) -> ConnectionDTO:
        """Create a test connection with the given parameters."""
        return ConnectionDTO(
            id=UUID(connection_id) if isinstance(connection_id, str) else connection_id,
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            target_user_id=UUID(target_user_id) if isinstance(target_user_id, str) else target_user_id,
            status=connection_status,
            created_at=kwargs.get('created_at') or datetime.utcnow(),
            updated_at=kwargs.get('updated_at') or datetime.utcnow(),
            **{k: v for k, v in kwargs.items() if k not in ['created_at', 'updated_at']}
        )

# Mock Service Factory
class MockServiceFactory:
    """Factory for creating mock services with consistent behavior."""
    
    @staticmethod
    def create_mock_auth_service(user: User = None):
        """Create a mock authentication service."""
        async def mock_get_current_user():
            return user or TestDataFactory.create_user()
        return mock_get_current_user
    
    @staticmethod
    def create_mock_connection_service(**service_overrides):
        """Create a mock connection service with optional overrides."""
        async def default_create_connection(user_id: str, target_user_id: str, status: str = "pending"):
            return TestDataFactory.create_connection(
                user_id=user_id,
                target_user_id=target_user_id,
                connection_status=status
            )
        
        async def default_get_connections(user_id: str, status: str = None):
            return [TestDataFactory.create_connection()]
        
        async def default_update_connection_status(connection_id: str, new_status: str, user_id: str):
            return TestDataFactory.create_connection(connection_status=new_status)
        
        async def default_delete_connection(connection_id: str, user_id: str):
            return {"message": "Connection deleted successfully"}
        
        services = {
            'create_connection': service_overrides.get('create_connection', default_create_connection),
            'get_connections': service_overrides.get('get_connections', default_get_connections),
            'update_connection_status': service_overrides.get('update_connection_status', default_update_connection_status),
            'delete_connection': service_overrides.get('delete_connection', default_delete_connection)
        }
        
        async def mock_get_connection_service():
            return services
        
        return mock_get_connection_service

# Test Helper
class TestHelper:
    """Helper class for common test operations."""
    
    @staticmethod
    def setup_mocks(user: User = None, **service_overrides):
        """Setup common mocks for tests."""
        app.dependency_overrides.clear()
        
        if user:
            app.dependency_overrides[get_current_user] = MockServiceFactory.create_mock_auth_service(user)
        
        if service_overrides:
            app.dependency_overrides[get_connection_service] = MockServiceFactory.create_mock_connection_service(**service_overrides)
    
    @staticmethod
    def cleanup_mocks():
        """Clean up all dependency overrides."""
        from app.core.security import get_current_user
        from app.api.connections import get_connection_service
        
        # Remove specific overrides
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        if get_connection_service in app.dependency_overrides:
            del app.dependency_overrides[get_connection_service]
    
    @staticmethod
    def assert_error_response(response, expected_status: int, expected_detail: str):
        """Assert error response format."""
        assert response.status_code == expected_status
        assert expected_detail in response.json()["detail"]

# Base Test Class
class BaseConnectionTest:
    """Base class for connection tests with common setup."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        with TestClient(app) as test_client:
            yield test_client
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Setup and cleanup for each test."""
        TestHelper.cleanup_mocks()
        yield
        TestHelper.cleanup_mocks()

# Test Classes
class TestCreateConnection(BaseConnectionTest):
    """Test cases for creating connections."""
    
    def test_create_connection_success(self, client):
        """Test successful connection creation."""
        user = TestDataFactory.create_user()
        TestHelper.setup_mocks(user=user)
        
        response = client.post(
            "/api/connections",
            json={"target_user_id": TestConstants.TARGET_USER_ID},
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == "pending"
        assert data["target_user_id"] == TestConstants.TARGET_USER_ID
    
    def test_create_connection_inactive_user(self, client):
        """Test creating connection as inactive user."""
        inactive_user = TestDataFactory.create_user(
            user_id=TestConstants.INACTIVE_USER_ID,
            is_active=False
        )
        TestHelper.setup_mocks(user=inactive_user)
        
        response = client.post(
            "/api/connections",
            json={"target_user_id": TestConstants.TARGET_USER_ID},
            headers={"Authorization": "Bearer test_token"}
        )
        
        TestHelper.assert_error_response(
            response,
            status.HTTP_400_BAD_REQUEST,
            "Inactive users cannot create connections"
        )
    
    def test_create_connection_self_target(self, client):
        """Test creating connection with self as target."""
        user = TestDataFactory.create_user()
        TestHelper.setup_mocks(user=user)
        
        response = client.post(
            "/api/connections",
            json={"target_user_id": str(user.id)},
            headers={"Authorization": "Bearer test_token"}
        )
        
        TestHelper.assert_error_response(
            response,
            status.HTTP_400_BAD_REQUEST,
            "Cannot create connection to yourself"
        )
    
    @pytest.mark.parametrize("exception_type,expected_status,expected_detail", [
        (ValueError("Connection already exists"), status.HTTP_400_BAD_REQUEST, "Connection already exists"),
        (HTTPException(status_code=409, detail="Conflict"), 409, "Conflict"),
        (Exception("Database error"), status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create connection"),
    ])
    def test_create_connection_error_handling(self, client, exception_type, expected_status, expected_detail):
        """Test error handling in connection creation."""
        async def failing_create_connection(*args, **kwargs):
            raise exception_type
        
        user = TestDataFactory.create_user()
        TestHelper.setup_mocks(
            user=user,
            create_connection=failing_create_connection
        )
        
        response = client.post(
            "/api/connections",
            json={"target_user_id": TestConstants.TARGET_USER_ID},
            headers={"Authorization": "Bearer test_token"}
        )
        
        TestHelper.assert_error_response(response, expected_status, expected_detail)

class TestGetConnections(BaseConnectionTest):
    """Test cases for retrieving connections."""
    
    def test_get_connections_success(self, client):
        """Test successful retrieval of connections."""
        user = TestDataFactory.create_user()
        connections = [
            TestDataFactory.create_connection(connection_status="pending"),
            TestDataFactory.create_connection(connection_id=str(uuid4()), connection_status="accepted")
        ]
        
        async def mock_get_connections(*args, **kwargs):
            return connections
        
        TestHelper.setup_mocks(
            user=user,
            get_connections=mock_get_connections
        )
        
        response = client.get(
            "/api/connections",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
    
    @pytest.mark.parametrize("status_filter,expected_count", [
        ("pending", 1),
        ("accepted", 1),
        (None, 2),
    ])
    def test_get_connections_with_status_filter(self, client, status_filter, expected_count):
        """Test retrieval with status filters."""
        user = TestDataFactory.create_user()
        all_connections = [
            TestDataFactory.create_connection(connection_status="pending"),
            TestDataFactory.create_connection(connection_id=str(uuid4()), connection_status="accepted")
        ]
        
        async def mock_get_connections(user_id: str, status: str = None):
            if status:
                return [c for c in all_connections if c.status == status]
            return all_connections
        
        TestHelper.setup_mocks(
            user=user,
            get_connections=mock_get_connections
        )
        
        url = "/api/connections"
        if status_filter:
            url += f"?connection_status={status_filter}"
        
        response = client.get(url, headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == expected_count
    
    @pytest.mark.parametrize("exception_type,expected_status,expected_detail", [
        (ValueError("Invalid status"), status.HTTP_400_BAD_REQUEST, "Invalid status"),
        (Exception("Database error"), status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to retrieve connections"),
    ])
    def test_get_connections_error_handling(self, client, exception_type, expected_status, expected_detail):
        """Test error handling in connection retrieval."""
        async def failing_get_connections(*args, **kwargs):
            raise exception_type
        
        user = TestDataFactory.create_user()
        TestHelper.setup_mocks(
            user=user,
            get_connections=failing_get_connections
        )
        
        response = client.get(
            "/api/connections",
            headers={"Authorization": "Bearer test_token"}
        )
        
        TestHelper.assert_error_response(response, expected_status, expected_detail)

class TestUpdateConnection(BaseConnectionTest):
    """Test cases for updating connections."""
    
    @pytest.mark.parametrize("new_status", ["accepted", "rejected"])
    def test_update_connection_success(self, client, new_status):
        """Test successful connection status update."""
        user = TestDataFactory.create_user()
        
        async def mock_update_connection_status(connection_id: str, new_status: str, user_id: str):
            return TestDataFactory.create_connection(connection_status=new_status)
        
        TestHelper.setup_mocks(
            user=user,
            update_connection_status=mock_update_connection_status
        )
        
        response = client.patch(
            f"/api/connections/{TestConstants.CONNECTION_ID}?status={new_status}",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == new_status
    
    @pytest.mark.parametrize("exception_type,expected_status,expected_detail", [
        (HTTPException(status_code=403, detail="Forbidden"), 403, "Forbidden"),
        (ValueError("Invalid transition"), status.HTTP_400_BAD_REQUEST, "Invalid transition"),
        (Exception("Database error"), status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to update connection"),
    ])
    def test_update_connection_error_handling(self, client, exception_type, expected_status, expected_detail):
        """Test error handling in connection updates."""
        async def failing_update_connection(*args, **kwargs):
            raise exception_type
        
        user = TestDataFactory.create_user()
        TestHelper.setup_mocks(
            user=user,
            update_connection_status=failing_update_connection
        )
        
        response = client.patch(
            f"/api/connections/{TestConstants.CONNECTION_ID}?status=accepted",
            headers={"Authorization": "Bearer test_token"}
        )
        
        TestHelper.assert_error_response(response, expected_status, expected_detail)

class TestDeleteConnection(BaseConnectionTest):
    """Test cases for deleting connections."""
    
    def test_delete_connection_success(self, client):
        """Test successful connection deletion."""
        user = TestDataFactory.create_user()
        
        async def mock_delete_connection(connection_id: str, user_id: str):
            return {"message": "Connection deleted successfully"}
        
        TestHelper.setup_mocks(
            user=user,
            delete_connection=mock_delete_connection
        )
        
        response = client.delete(
            f"/api/connections/{TestConstants.CONNECTION_ID}",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "deleted successfully" in data["message"]
    
    def test_delete_connection_invalid_uuid(self, client):
        """Test deletion with invalid UUID."""
        user = TestDataFactory.create_user()
        TestHelper.setup_mocks(user=user)
        
        response = client.delete(
            "/api/connections/invalid-uuid",
            headers={"Authorization": "Bearer test_token"}
        )
        
        TestHelper.assert_error_response(
            response,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Invalid UUID format"
        )
    
    @pytest.mark.parametrize("exception_type,expected_status,expected_detail", [
        (HTTPException(status_code=404, detail="Not found"), 404, "Not found"),
        (HTTPException(status_code=403, detail="Forbidden"), 403, "Forbidden"),
        (Exception("Database error"), status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to delete connection"),
    ])
    def test_delete_connection_error_handling(self, client, exception_type, expected_status, expected_detail):
        """Test error handling in connection deletion."""
        async def failing_delete_connection(*args, **kwargs):
            raise exception_type
        
        user = TestDataFactory.create_user()
        TestHelper.setup_mocks(
            user=user,
            delete_connection=failing_delete_connection
        )
        
        response = client.delete(
            f"/api/connections/{TestConstants.CONNECTION_ID}",
            headers={"Authorization": "Bearer test_token"}
        )
        
        TestHelper.assert_error_response(response, expected_status, expected_detail)

class TestConnectionsCoverage(BaseConnectionTest):
    """Additional tests to ensure 100% code coverage."""
    
    def test_get_connection_service_function(self):
        """Test the get_connection_service function directly."""
        import asyncio
        
        async def test_service():
            service = await get_connection_service()
            assert 'create_connection' in service
            assert 'get_connections' in service
            assert 'update_connection_status' in service
            assert 'delete_connection' in service
        
        asyncio.run(test_service())

# Authentication Tests
class TestAuthentication(BaseConnectionTest):
    """Test authentication scenarios across all endpoints."""
    
    @pytest.mark.parametrize("endpoint,method,data", [
        ("/api/connections", "POST", {"target_user_id": TestConstants.TARGET_USER_ID}),
        ("/api/connections", "GET", None),
        (f"/api/connections/{TestConstants.CONNECTION_ID}?status=accepted", "PATCH", None),
        (f"/api/connections/{TestConstants.CONNECTION_ID}", "DELETE", None),
    ])
    def test_endpoints_require_authentication(self, client, endpoint, method, data):
        """Test that all endpoints require authentication."""
        # Clear all overrides first
        app.dependency_overrides.clear()
        
        # Mock auth to raise HTTPException for invalid token
        async def mock_auth_failure():
            raise HTTPException(status_code=401, detail="Invalid token")
        
        app.dependency_overrides[get_current_user] = mock_auth_failure
        
        kwargs = {"headers": {"Authorization": "Bearer invalid_token"}}
        if data:
            kwargs["json"] = data
        
        response = getattr(client, method.lower())(endpoint, **kwargs)
        
        # Should get 401 for authentication failure
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in response.json()["detail"]
