# tests/test_notification_api.py
import pytest
from fastapi import status, FastAPI
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import UUID, uuid4
from typing import List, Dict, Any

from app.models.schemas import User, NotificationDTO
from app.api import notification as notification_router

# Mock user for testing
mock_user = User(
    id=uuid4(),
    email="test@example.com",
    first_name="Test",
    last_name="User",
    is_active=True,
    is_verified=True,
    role="user",
    hashed_password="hashed_password"
)

# Create a notification dictionary for testing
@pytest.fixture
def test_notification():
    now = datetime.now(timezone.utc)
    notification_dict = {
        "id": str(uuid4()),
        "user_id": str(mock_user.id),
        "title": "Test Notification",
        "message": "Test notification",
        "is_read": False,
        "notification_type": "info",
        "metadata": {},
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    return notification_dict

# Fixture for the FastAPI app with overridden dependencies
@pytest.fixture
def app():
    app = FastAPI()
    
    # Mock the get_current_user dependency
    async def mock_get_current_user():
        return mock_user
    
    # Override the dependency in the router
    app.dependency_overrides[notification_router.get_current_user] = mock_get_current_user
    
    app.include_router(notification_router.router)
    return app

# Fixture for the test client
@pytest.fixture
def client(app):
    return TestClient(app)

# Helper function to create a notification DTO from a dict
def create_notification_dto(notification_dict: dict) -> dict:
    """Helper to create a notification DTO from a dictionary"""
    return {
        "id": notification_dict["id"],
        "user_id": notification_dict["user_id"],
        "title": notification_dict["title"],
        "message": notification_dict["message"],
        "is_read": notification_dict["is_read"],
        "notification_type": notification_dict["notification_type"],
        "metadata": notification_dict.get("metadata", {}),
        "created_at": notification_dict["created_at"],
        "updated_at": notification_dict["updated_at"]
    }

# Test cases
def test_get_notifications(client, test_notification):
    with patch("app.api.notification.get_notifications_svc") as mock_get:
        # The service layer returns a list of notification dictionaries
        mock_get.return_value = [create_notification_dto(test_notification)]
        
        response = client.get(
            "/api/notifications",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Notification"
        mock_get.assert_called_once()

def test_mark_notification_as_read(client, test_notification):
    # Update the notification
    test_notification["is_read"] = True
    notification_id = test_notification["id"]
    
    with patch("app.api.notification.mark_as_read_svc") as mock_mark:
        # The service returns an updated notification dictionary
        mock_mark.return_value = create_notification_dto(test_notification)
        
        response = client.put(
            f"/api/notifications/{notification_id}/read",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_read"] is True
        mock_mark.assert_called_once_with(UUID(notification_id), mock_user.id)

def test_mark_all_notifications_as_read(client):
    with patch("app.api.notification.mark_all_as_read_svc") as mock_mark_all:
        mock_mark_all.return_value = 2  # Number of notifications marked as read
        
        response = client.put(
            "/api/notifications/read-all",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "2" in data["message"]  # Check that the count is in the message
        mock_mark_all.assert_called_once_with(mock_user.id)


# Additional comprehensive tests

# Global fixtures for notification tests
@pytest.fixture
def notification_payload_builder():
    """Refactor repeated payload builders into utility functions."""
    def _build_notification_payload(**kwargs):
        base_payload = {
            "title": "Test Notification",
            "message": "Test message",
            "notification_type": "info",
            "metadata": {}
        }
        base_payload.update(kwargs)
        return base_payload
    return _build_notification_payload

@pytest.fixture
def mock_notification_responses(test_notification):
    """Centralized mock responses."""
    return {
        "get_notifications": [create_notification_dto(test_notification)],
        "get_notification": create_notification_dto(test_notification),
        "create_notification": create_notification_dto(test_notification),
        "mark_as_read": create_notification_dto({**test_notification, "is_read": True}),
        "mark_all_count": 3
    }

class TestNotificationApiCoverage:
    """Test class focused on covering specific lines in notification.py API endpoints."""

    def test_get_notifications_exception_handling(self, client, mock_notification_responses):
        """Test lines 52-53 - Exception handling in get_notifications."""
        with patch("app.api.notification.get_notifications_svc") as mock_get:
            # Test general Exception handling (lines 52-53)
            mock_get.side_effect = Exception("Service unavailable")
            
            response = client.get("/api/notifications")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to retrieve notifications: Service unavailable" in response.json()["detail"]
    
    def test_get_notifications_with_query_parameters(self, client, mock_notification_responses):
        """Test get_notifications with various query parameters."""
        with patch("app.api.notification.get_notifications_svc") as mock_get:
            mock_get.return_value = mock_notification_responses["get_notifications"]
            
            # Test with all query parameters
            response = client.get("/api/notifications?skip=10&limit=5&unread_only=true")
            assert response.status_code == status.HTTP_200_OK
            
            # Verify service was called with correct parameters
            mock_get.assert_called_once_with(
                user_id=mock_user.id,
                skip=10,
                limit=5,
                unread_only=True
            )

    def test_get_notification_not_found_handling(self, client):
        """Test lines 76-87 - get_notification not found and exception handling."""
        notification_id = str(uuid4())
        
        with patch("app.api.notification.get_notification_svc") as mock_get:
            # Test notification not found scenario (lines 78-82)
            mock_get.return_value = None
            
            response = client.get(f"/api/notifications/{notification_id}")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Notification not found or access denied" in response.json()["detail"]
    
    def test_get_notification_http_exception_handling(self, client):
        """Test lines 84-85 - HTTPException re-raising in get_notification."""
        from fastapi import HTTPException
        notification_id = str(uuid4())
        
        with patch("app.api.notification.get_notification_svc") as mock_get:
            # Test HTTPException re-raising (lines 84-85)
            mock_get.side_effect = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
            
            response = client.get(f"/api/notifications/{notification_id}")
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Access denied" in response.json()["detail"]
    
    def test_get_notification_general_exception_handling(self, client):
        """Test lines 86-90 - General exception handling in get_notification."""
        notification_id = str(uuid4())
        
        with patch("app.api.notification.get_notification_svc") as mock_get:
            # Test general Exception handling (lines 86-90)
            mock_get.side_effect = Exception("Database error")
            
            response = client.get(f"/api/notifications/{notification_id}")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to retrieve notification: Database error" in response.json()["detail"]

    def test_create_notification_success(self, client, notification_payload_builder, mock_notification_responses):
        """Test lines 107-113 - create_notification success flow."""
        with patch("app.api.notification.create_notification_svc") as mock_create:
            # Test successful creation (lines 107-113)
            mock_create.return_value = mock_notification_responses["create_notification"]
            
            payload = notification_payload_builder()
            response = client.post("/api/notifications", json=payload)
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["title"] == payload["title"]
            
            # Verify service was called with correct parameters
            mock_create.assert_called_once_with(
                user_id=mock_user.id,
                **payload
            )
    
    def test_create_notification_exception_handling(self, client, notification_payload_builder):
        """Test lines 112-116 - Exception handling in create_notification."""
        with patch("app.api.notification.create_notification_svc") as mock_create:
            # Test general Exception handling (lines 112-116)
            mock_create.side_effect = Exception("Creation failed")
            
            payload = notification_payload_builder()
            response = client.post("/api/notifications", json=payload)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create notification: Creation failed" in response.json()["detail"]

    def test_mark_notification_as_read_http_exception_handling(self, client):
        """Test lines 135-138 - HTTPException handling in mark_as_read."""
        from fastapi import HTTPException
        notification_id = str(uuid4())
        
        with patch("app.api.notification.mark_as_read_svc") as mock_mark:
            # Test HTTPException re-raising (lines 135-136)
            mock_mark.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
            
            response = client.put(f"/api/notifications/{notification_id}/read")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Notification not found" in response.json()["detail"]
    
    def test_mark_notification_as_read_general_exception_handling(self, client):
        """Test lines 137-141 - General exception handling in mark_as_read."""
        notification_id = str(uuid4())
        
        with patch("app.api.notification.mark_as_read_svc") as mock_mark:
            # Test general Exception handling (lines 137-141)
            mock_mark.side_effect = Exception("Update failed")
            
            response = client.put(f"/api/notifications/{notification_id}/read")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to mark notification as read: Update failed" in response.json()["detail"]

    def test_mark_all_notifications_as_read_success(self, client):
        """Test lines 159-160 - mark_all_as_read success flow."""
        with patch("app.api.notification.mark_all_as_read_svc") as mock_mark_all:
            # Test successful mark all (lines 157-158)
            mock_mark_all.return_value = 5
            
            response = client.put("/api/notifications/read-all")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["message"] == "Marked 5 notifications as read"
            mock_mark_all.assert_called_once_with(mock_user.id)
    
    def test_mark_all_notifications_as_read_exception_handling(self, client):
        """Test lines 159-163 - Exception handling in mark_all_as_read."""
        with patch("app.api.notification.mark_all_as_read_svc") as mock_mark_all:
            # Test general Exception handling (lines 159-163)
            mock_mark_all.side_effect = Exception("Bulk update failed")
            
            response = client.put("/api/notifications/read-all")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to mark notifications as read: Bulk update failed" in response.json()["detail"]

    def test_delete_notification_success(self, client):
        """Test lines 177-182 - delete_notification success flow."""
        notification_id = str(uuid4())
        
        with patch("app.api.notification.delete_notification_svc") as mock_delete:
            # Test successful deletion (line 178)
            mock_delete.return_value = None
            
            response = client.delete(f"/api/notifications/{notification_id}")
            
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_delete.assert_called_once_with(UUID(notification_id), mock_user.id)
    
    def test_delete_notification_http_exception_handling(self, client):
        """Test lines 179-180 - HTTPException handling in delete_notification."""
        from fastapi import HTTPException
        notification_id = str(uuid4())
        
        with patch("app.api.notification.delete_notification_svc") as mock_delete:
            # Test HTTPException re-raising (lines 179-180)
            mock_delete.side_effect = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete notification"
            )
            
            response = client.delete(f"/api/notifications/{notification_id}")
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Cannot delete notification" in response.json()["detail"]
    
    def test_delete_notification_general_exception_handling(self, client):
        """Test lines 181-185 - General exception handling in delete_notification."""
        notification_id = str(uuid4())
        
        with patch("app.api.notification.delete_notification_svc") as mock_delete:
            # Test general Exception handling (lines 181-185)
            mock_delete.side_effect = Exception("Delete operation failed")
            
            response = client.delete(f"/api/notifications/{notification_id}")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to delete notification: Delete operation failed" in response.json()["detail"]


class TestNotificationApiEndpointIntegration:
    """Ensure each test class interfaces with only one endpoint."""
    
    def test_get_notification_success_flow(self, client, test_notification):
        """Test complete success flow for get_notification endpoint."""
        notification_id = test_notification["id"]
        
        with patch("app.api.notification.get_notification_svc") as mock_get:
            mock_get.return_value = create_notification_dto(test_notification)
            
            response = client.get(f"/api/notifications/{notification_id}")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == notification_id
            assert data["title"] == test_notification["title"]
            mock_get.assert_called_once_with(UUID(notification_id), mock_user.id)
    
    def test_create_notification_with_metadata(self, client, notification_payload_builder):
        """Test create_notification with custom metadata."""
        with patch("app.api.notification.create_notification_svc") as mock_create:
            payload = notification_payload_builder(
                metadata={"priority": "high", "category": "system"}
            )
            mock_create.return_value = create_notification_dto({
                "id": str(uuid4()),
                "user_id": str(mock_user.id),
                **payload,
                "is_read": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            
            response = client.post("/api/notifications", json=payload)
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["metadata"]["priority"] == "high"
            assert data["metadata"]["category"] == "system"


class TestNotificationApiQueryParameters:
    """Skip tests for deprecated endpoints, focus on active functionality."""
    
    def test_get_notifications_with_pagination(self, client, mock_notification_responses):
        """Test get_notifications with pagination parameters."""
        with patch("app.api.notification.get_notifications_svc") as mock_get:
            mock_get.return_value = mock_notification_responses["get_notifications"]
            
            response = client.get("/api/notifications?skip=0&limit=10")
            assert response.status_code == status.HTTP_200_OK
            
            mock_get.assert_called_once_with(
                user_id=mock_user.id,
                skip=0,
                limit=10,
                unread_only=False
            )
    
    def test_get_notifications_unread_only_filter(self, client, mock_notification_responses):
        """Test get_notifications with unread_only filter."""
        with patch("app.api.notification.get_notifications_svc") as mock_get:
            mock_get.return_value = mock_notification_responses["get_notifications"]
            
            response = client.get("/api/notifications?unread_only=true")
            assert response.status_code == status.HTTP_200_OK
            
            mock_get.assert_called_once_with(
                user_id=mock_user.id,
                skip=0,
                limit=10,
                unread_only=True
            )