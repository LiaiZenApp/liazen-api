"""
Notification Service

This module provides services for managing user notifications.
"""
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import HTTPException, status

from app.models.schemas import NotificationDTO

# In-memory storage for demonstration purposes
# In a real application, this would be a database
db_notifications = {}


async def get_notifications(
    user_id: UUID,
    skip: int = 0,
    limit: int = 10,
    unread_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Get a list of notifications for a user
    
    Args:
        user_id: ID of the user
        skip: Number of records to skip
        limit: Maximum number of records to return
        unread_only: Whether to return only unread notifications
        
    Returns:
        List of notifications
    """
    notifications = [
        notif for notif in db_notifications.values()
        if notif["user_id"] == str(user_id)
    ]
    
    if unread_only:
        notifications = [n for n in notifications if not n["is_read"]]
    
    return notifications[skip:skip + limit]


async def get_notification(
    notification_id: UUID,
    user_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Get a specific notification by ID
    
    Args:
        notification_id: ID of the notification
        user_id: ID of the user making the request
        
    Returns:
        The notification if found, None otherwise
        
    Raises:
        HTTPException: If the notification is not found or not accessible
    """
    notification = db_notifications.get(str(notification_id))
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
        
    if notification["user_id"] != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this notification"
        )
        
    return notification


async def create_notification(
    user_id: UUID,
    title: str,
    message: str,
    notification_type: str = "info",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new notification
    
    Args:
        user_id: ID of the user to notify
        title: Notification title
        message: Notification message
        notification_type: Type of notification (e.g., 'info', 'warning', 'error')
        metadata: Additional metadata for the notification
        
    Returns:
        The created notification
    """
    from uuid import uuid4
    
    notification_id = str(uuid4())
    now = datetime.utcnow()
    
    notification = {
        "id": notification_id,
        "user_id": str(user_id),
        "title": title,
        "message": message,
        "notification_type": notification_type,
        "is_read": False,
        "metadata": metadata or {},
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    db_notifications[notification_id] = notification
    return notification


async def mark_as_read(notification_id: UUID, user_id: UUID) -> Dict[str, Any]:
    """
    Mark a notification as read
    
    Args:
        notification_id: ID of the notification to mark as read
        user_id: ID of the user making the request
        
    Returns:
        The updated notification
        
    Raises:
        HTTPException: If the notification is not found or not accessible
    """
    notification = await get_notification(notification_id, user_id)
    
    if notification["is_read"]:
        return notification
        
    notification["is_read"] = True
    notification["updated_at"] = datetime.utcnow().isoformat()
    
    return notification


async def mark_all_as_read(user_id: UUID) -> int:
    """
    Mark all notifications as read for a user
    
    Args:
        user_id: ID of the user
        
    Returns:
        Number of notifications marked as read
    """
    count = 0
    now = datetime.utcnow().isoformat()
    
    for notification in db_notifications.values():
        if notification["user_id"] == str(user_id) and not notification["is_read"]:
            notification["is_read"] = True
            notification["updated_at"] = now
            count += 1
            
    return count


async def delete_notification(notification_id: UUID, user_id: UUID) -> None:
    """
    Delete a notification
    
    Args:
        notification_id: ID of the notification to delete
        user_id: ID of the user making the request
        
    Raises:
        HTTPException: If the notification is not found or not accessible
    """
    # This will raise an exception if the notification doesn't exist or isn't accessible
    await get_notification(notification_id, user_id)
    
    # If we get here, the notification exists and is accessible
    del db_notifications[str(notification_id)]


# Add some test notifications for demonstration
if not db_notifications:
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    
    test_notifications = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "user_id": "00000000-0000-0000-0000-000000000000",
            "title": "Welcome to Our App!",
            "message": "Thank you for signing up. We're glad to have you on board!",
            "notification_type": "info",
            "is_read": True,
            "metadata": {"action_url": "/welcome"},
            "created_at": (now - timedelta(days=2)).isoformat(),
            "updated_at": (now - timedelta(days=2)).isoformat()
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "user_id": "00000000-0000-0000-0000-000000000000",
            "title": "New Feature Available",
            "message": "Check out our latest feature that helps you connect with friends!",
            "notification_type": "info",
            "is_read": False,
            "metadata": {"feature": "friend_connections"},
            "created_at": (now - timedelta(hours=5)).isoformat(),
            "updated_at": (now - timedelta(hours=5)).isoformat()
        },
        {
            "id": "33333333-3333-3333-3333-333333333333",
            "user_id": "00000000-0000-0000-0000-000000000000",
            "title": "Reminder: Event Tomorrow",
            "message": "Don't forget about the event you signed up for tomorrow at 2 PM.",
            "notification_type": "reminder",
            "is_read": False,
            "metadata": {"event_id": "event123", "time": "2023-06-06T14:00:00Z"},
            "created_at": (now - timedelta(hours=2)).isoformat(),
            "updated_at": (now - timedelta(hours=2)).isoformat()
        }
    ]
    
    for notification in test_notifications:
        db_notifications[notification["id"]] = notification
