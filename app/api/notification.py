"""
Notification API

This module provides API endpoints for managing user notifications.
"""
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer

from app.models.schemas import User, NotificationDTO
from app.services.notification_service import (
    get_notifications as get_notifications_svc,
    get_notification as get_notification_svc,
    mark_as_read as mark_as_read_svc,
    mark_all_as_read as mark_all_as_read_svc,
    delete_notification as delete_notification_svc,
    create_notification as create_notification_svc
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])
security = HTTPBearer()

@router.get("", response_model=List[NotificationDTO])
async def get_notifications(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    unread_only: bool = Query(False, description="Return only unread notifications"),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of notifications for the current user
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        unread_only: Whether to return only unread notifications
        current_user: The authenticated user (injected dependency)
        
    Returns:
        List of notifications
    """
    try:
        return await get_notifications_svc(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            unread_only=unread_only
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notifications: {str(e)}"
        )

@router.get("/{notification_id}", response_model=NotificationDTO)
async def get_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific notification by ID
    
    Args:
        notification_id: ID of the notification to retrieve
        current_user: The authenticated user (injected dependency)
        
    Returns:
        The requested notification
        
    Raises:
        HTTPException: If the notification is not found or not accessible
    """
    try:
        notification = await get_notification_svc(notification_id, current_user.id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or access denied"
            )
        return notification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notification: {str(e)}"
        )

@router.post("", status_code=status.HTTP_201_CREATED, response_model=NotificationDTO)
async def create_notification(
    notification_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new notification
    
    Args:
        notification_data: Notification data
        current_user: The authenticated user (injected dependency)
        
    Returns:
        The created notification
    """
    try:
        return await create_notification_svc(
            user_id=current_user.id,
            **notification_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}"
        )

@router.put("/{notification_id}/read", response_model=NotificationDTO)
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Mark a notification as read
    
    Args:
        notification_id: ID of the notification to mark as read
        current_user: The authenticated user (injected dependency)
        
    Returns:
        The updated notification
    """
    try:
        return await mark_as_read_svc(notification_id, current_user.id)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )

@router.put("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user)
):
    """
    Mark all notifications as read for the current user
    
    Args:
        current_user: The authenticated user (injected dependency)
        
    Returns:
        Success message
    """
    try:
        count = await mark_all_as_read_svc(current_user.id)
        return {"message": f"Marked {count} notifications as read"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notifications as read: {str(e)}"
        )

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a notification
    
    Args:
        notification_id: ID of the notification to delete
        current_user: The authenticated user (injected dependency)
    """
    try:
        await delete_notification_svc(notification_id, current_user.id)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )
