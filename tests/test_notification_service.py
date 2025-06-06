"""
Test coverage for app/services/notification_service.py

This module provides comprehensive test coverage for the notification service.
"""
import pytest
from unittest.mock import patch, MagicMock
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import HTTPException, status

from app.services.notification_service import (
    get_notifications, get_notification, create_notification,
    mark_as_read, mark_all_as_read, delete_notification, db_notifications
)




class TestNotificationServiceSpecificLineCoverage:
    """Test specific uncovered lines in notification service."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Clear notifications database before each test."""
        db_notifications.clear()
    
    @pytest.mark.asyncio
    async def test_get_notifications_unread_filter_lines_37_45(self):
        """Test lines 37-45: get_notifications with unread_only filter."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        # Create test notifications
        read_notif = {
            "id": "read-notif-id",
            "user_id": str(user_id),
            "title": "Read Notification",
            "message": "This is read",
            "is_read": True
        }
        unread_notif = {
            "id": "unread-notif-id", 
            "user_id": str(user_id),
            "title": "Unread Notification",
            "message": "This is unread",
            "is_read": False
        }
        
        db_notifications["read-notif-id"] = read_notif
        db_notifications["unread-notif-id"] = unread_notif
        
        # Test unread_only=True
        unread_results = await get_notifications(user_id, unread_only=True)
        assert len(unread_results) == 1
        assert unread_results[0]["id"] == "unread-notif-id"
        
        # Test unread_only=False (default)
        all_results = await get_notifications(user_id, unread_only=False)
        assert len(all_results) == 2
    
    @pytest.mark.asyncio
    async def test_get_notifications_pagination_line_45(self):
        """Test line 45: get_notifications pagination logic."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        # Create multiple notifications
        for i in range(5):
            notif = {
                "id": f"notif-{i}",
                "user_id": str(user_id),
                "title": f"Notification {i}",
                "message": f"Message {i}",
                "is_read": False
            }
            db_notifications[f"notif-{i}"] = notif
        
        # Test pagination
        page1 = await get_notifications(user_id, skip=0, limit=2)
        assert len(page1) == 2
        
        page2 = await get_notifications(user_id, skip=2, limit=2)
        assert len(page2) == 2
        
        page3 = await get_notifications(user_id, skip=4, limit=2)
        assert len(page3) == 1
    
    @pytest.mark.asyncio
    async def test_get_notification_not_found_lines_65_71(self):
        """Test lines 65-71: get_notification raises HTTPException when not found."""
        notification_id = UUID("00000000-0000-0000-0000-000000000000")
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_notification(notification_id, user_id)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Notification not found"
    
    @pytest.mark.asyncio
    async def test_get_notification_unauthorized_lines_73_77(self):
        """Test lines 73-77: get_notification raises HTTPException when unauthorized."""
        notification_id = UUID("11111111-1111-1111-1111-111111111111")
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        other_user_id = UUID("87654321-4321-4321-4321-210987654321")
        
        # Create notification for different user
        notification = {
            "id": str(notification_id),
            "user_id": str(other_user_id),
            "title": "Private Notification",
            "message": "This belongs to another user",
            "is_read": False
        }
        db_notifications[str(notification_id)] = notification
        
        with pytest.raises(HTTPException) as exc_info:
            await get_notification(notification_id, user_id)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Not authorized to access this notification"
    
    @pytest.mark.asyncio
    async def test_get_notification_success_line_79(self):
        """Test line 79: get_notification returns notification when authorized."""
        notification_id = UUID("11111111-1111-1111-1111-111111111111")
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        notification = {
            "id": str(notification_id),
            "user_id": str(user_id),
            "title": "Test Notification",
            "message": "Test message",
            "is_read": False
        }
        db_notifications[str(notification_id)] = notification
        
        result = await get_notification(notification_id, user_id)
        assert result == notification
    
    @pytest.mark.asyncio
    async def test_create_notification_lines_102_120(self):
        """Test lines 102-120: create_notification success flow."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        title = "Test Title"
        message = "Test Message"
        notification_type = "warning"
        metadata = {"key": "value"}
        
        result = await create_notification(user_id, title, message, notification_type, metadata)
        
        # Verify notification structure
        assert "id" in result
        assert result["user_id"] == str(user_id)
        assert result["title"] == title
        assert result["message"] == message
        assert result["notification_type"] == notification_type
        assert result["is_read"] is False
        assert result["metadata"] == metadata
        assert "created_at" in result
        assert "updated_at" in result
        
        # Verify storage
        assert result["id"] in db_notifications
        assert db_notifications[result["id"]] == result
    
    @pytest.mark.asyncio
    async def test_create_notification_default_values_lines_102_120(self):
        """Test lines 102-120: create_notification with default values."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        title = "Default Test"
        message = "Default Message"
        
        result = await create_notification(user_id, title, message)
        
        assert result["notification_type"] == "info"  # Default value
        assert result["metadata"] == {}  # Default empty dict
    
    @pytest.mark.asyncio
    async def test_mark_as_read_already_read_lines_137_140(self):
        """Test lines 137-140: mark_as_read when notification already read."""
        notification_id = UUID("11111111-1111-1111-1111-111111111111")
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        # Create already read notification
        notification = {
            "id": str(notification_id),
            "user_id": str(user_id),
            "title": "Already Read",
            "message": "This is already read",
            "is_read": True,
            "updated_at": "2023-01-01T00:00:00"
        }
        db_notifications[str(notification_id)] = notification
        
        result = await mark_as_read(notification_id, user_id)
        
        # Should return notification unchanged
        assert result["is_read"] is True
        assert result["updated_at"] == "2023-01-01T00:00:00"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_mark_as_read_success_lines_142_145(self):
        """Test lines 142-145: mark_as_read success flow."""
        notification_id = UUID("11111111-1111-1111-1111-111111111111")
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        # Create unread notification
        notification = {
            "id": str(notification_id),
            "user_id": str(user_id),
            "title": "Unread",
            "message": "This is unread",
            "is_read": False,
            "updated_at": "2023-01-01T00:00:00"
        }
        db_notifications[str(notification_id)] = notification
        
        result = await mark_as_read(notification_id, user_id)
        
        # Should be marked as read with updated timestamp
        assert result["is_read"] is True
        assert result["updated_at"] != "2023-01-01T00:00:00"  # Updated
    
    @pytest.mark.asyncio
    async def test_mark_all_as_read_lines_158_167(self):
        """Test lines 158-167: mark_all_as_read success flow."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        other_user_id = UUID("87654321-4321-4321-4321-210987654321")
        
        # Create notifications for target user (some read, some unread)
        notifications = [
            {
                "id": "unread1",
                "user_id": str(user_id),
                "is_read": False,
                "updated_at": "2023-01-01T00:00:00"
            },
            {
                "id": "unread2", 
                "user_id": str(user_id),
                "is_read": False,
                "updated_at": "2023-01-01T00:00:00"
            },
            {
                "id": "already_read",
                "user_id": str(user_id),
                "is_read": True,
                "updated_at": "2023-01-01T00:00:00"
            },
            {
                "id": "other_user",
                "user_id": str(other_user_id),
                "is_read": False,
                "updated_at": "2023-01-01T00:00:00"
            }
        ]
        
        for notif in notifications:
            db_notifications[notif["id"]] = notif
        
        count = await mark_all_as_read(user_id)
        
        # Should mark 2 unread notifications as read
        assert count == 2
        
        # Verify notifications were updated
        assert db_notifications["unread1"]["is_read"] is True
        assert db_notifications["unread2"]["is_read"] is True
        assert db_notifications["already_read"]["is_read"] is True  # Unchanged
        assert db_notifications["other_user"]["is_read"] is False  # Other user unchanged
    
    @pytest.mark.asyncio
    async def test_delete_notification_lines_182_185(self):
        """Test lines 182-185: delete_notification success flow."""
        notification_id = UUID("11111111-1111-1111-1111-111111111111")
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        # Create notification
        notification = {
            "id": str(notification_id),
            "user_id": str(user_id),
            "title": "To Delete",
            "message": "This will be deleted",
            "is_read": False
        }
        db_notifications[str(notification_id)] = notification
        
        # Delete notification
        await delete_notification(notification_id, user_id)
        
        # Verify deletion
        assert str(notification_id) not in db_notifications


class TestNotificationServiceTestData:
    """Test the test data initialization."""
    
    @patch('app.services.notification_service.db_notifications', {})
    def test_test_data_initialization_lines_189_231(self):
        """Test lines 189-231: test data initialization when db is empty."""
        # Import the module to trigger initialization
        import importlib
        import app.services.notification_service
        importlib.reload(app.services.notification_service)
        
        # Verify test notifications were created
        from app.services.notification_service import db_notifications
        
        assert len(db_notifications) == 3
        
        # Verify specific test notifications
        welcome_notif = db_notifications.get("11111111-1111-1111-1111-111111111111")
        assert welcome_notif is not None
        assert welcome_notif["title"] == "Welcome to Our App!"
        assert welcome_notif["is_read"] is True
        
        feature_notif = db_notifications.get("22222222-2222-2222-2222-222222222222")
        assert feature_notif is not None
        assert feature_notif["title"] == "New Feature Available"
        assert feature_notif["is_read"] is False
        
        reminder_notif = db_notifications.get("33333333-3333-3333-3333-333333333333")
        assert reminder_notif is not None
        assert reminder_notif["title"] == "Reminder: Event Tomorrow"
        assert reminder_notif["is_read"] is False


class TestNotificationServiceEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Clear notifications database before each test."""
        db_notifications.clear()
    
    @pytest.mark.asyncio
    async def test_get_notifications_empty_database(self):
        """Test get_notifications with empty database."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        result = await get_notifications(user_id)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_notifications_no_user_notifications(self):
        """Test get_notifications when user has no notifications."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        other_user_id = UUID("87654321-4321-4321-4321-210987654321")
        
        # Create notification for different user
        notification = {
            "id": "other-notif",
            "user_id": str(other_user_id),
            "title": "Other User Notification",
            "message": "Not for target user",
            "is_read": False
        }
        db_notifications["other-notif"] = notification
        
        result = await get_notifications(user_id)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_notifications_large_skip_value(self):
        """Test get_notifications with skip value larger than available notifications."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        # Create one notification
        notification = {
            "id": "single-notif",
            "user_id": str(user_id),
            "title": "Single Notification",
            "message": "Only one",
            "is_read": False
        }
        db_notifications["single-notif"] = notification
        
        result = await get_notifications(user_id, skip=10, limit=5)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_create_notification_none_metadata(self):
        """Test create_notification with None metadata."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        result = await create_notification(user_id, "Test", "Message", metadata=None)
        assert result["metadata"] == {}
    
    @pytest.mark.asyncio
    async def test_mark_all_as_read_no_notifications(self):
        """Test mark_all_as_read when user has no notifications."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        count = await mark_all_as_read(user_id)
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_mark_all_as_read_all_already_read(self):
        """Test mark_all_as_read when all notifications are already read."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        # Create already read notification
        notification = {
            "id": "already-read",
            "user_id": str(user_id),
            "is_read": True,
            "updated_at": "2023-01-01T00:00:00"
        }
        db_notifications["already-read"] = notification
        
        count = await mark_all_as_read(user_id)
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_delete_notification_calls_get_notification(self):
        """Test that delete_notification calls get_notification for validation."""
        notification_id = UUID("11111111-1111-1111-1111-111111111111")
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        # Test with non-existent notification
        with pytest.raises(HTTPException):
            await delete_notification(notification_id, user_id)
        
        # Test with unauthorized access
        other_user_id = UUID("87654321-4321-4321-4321-210987654321")
        notification = {
            "id": str(notification_id),
            "user_id": str(other_user_id),
            "title": "Other User",
            "message": "Not accessible",
            "is_read": False
        }
        db_notifications[str(notification_id)] = notification
        
        with pytest.raises(HTTPException):
            await delete_notification(notification_id, user_id)


class TestNotificationServiceDataTypes:
    """Test various data types and UUID handling."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Clear notifications database before each test."""
        db_notifications.clear()
    
    @pytest.mark.asyncio
    async def test_uuid_string_conversion(self):
        """Test that UUIDs are properly converted to strings."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        result = await create_notification(user_id, "Test", "Message")
        
        # user_id should be stored as string
        assert isinstance(result["user_id"], str)
        assert result["user_id"] == str(user_id)
    
    @pytest.mark.asyncio
    async def test_datetime_iso_format(self):
        """Test that datetime objects are stored in ISO format."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        result = await create_notification(user_id, "Test", "Message")
        
        # Timestamps should be ISO format strings
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)
        
        # Should be parseable as datetime
        datetime.fromisoformat(result["created_at"])
        datetime.fromisoformat(result["updated_at"])
    
    @pytest.mark.asyncio
    async def test_notification_id_generation(self):
        """Test that notification IDs are properly generated."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        
        result1 = await create_notification(user_id, "Test 1", "Message 1")
        result2 = await create_notification(user_id, "Test 2", "Message 2")
        
        # IDs should be different
        assert result1["id"] != result2["id"]
        
        # IDs should be valid UUID strings
        UUID(result1["id"])  # Should not raise exception
        UUID(result2["id"])  # Should not raise exception