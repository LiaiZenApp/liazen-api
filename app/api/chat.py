from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID

from app.models.schemas import MessageRequest, MessageDTO, User
from app.services.chat_service import send_message as send_message_svc, get_messages as get_messages_svc
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/messages", response_model=MessageDTO, status_code=status.HTTP_201_CREATED)
async def send_message(
    message: MessageRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a chat message
    
    Args:
        message: The message to send
        current_user: The authenticated user
        
    Returns:
        MessageDTO: The sent message
    """
    try:
        sent_message = await send_message_svc(
            sender_id=str(current_user.id),
            recipient_id=message.recipient_id,
            content=message.content,
            metadata=message.metadata or {}
        )
        return sent_message
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@router.get("/messages", response_model=List[MessageDTO])
async def get_messages(
    recipient_id: str = Query(..., description="ID of the user to get messages with"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_current_user)
):
    """
    Get messages between the current user and another user
    
    Args:
        recipient_id: ID of the other user
        limit: Maximum number of messages to return (1-100)
        offset: Number of messages to skip
        current_user: The authenticated user
        
    Returns:
        List[MessageDTO]: List of messages
    """
    try:
        messages = await get_messages_svc(
            user_id=str(current_user.id),
            recipient_id=recipient_id,
            limit=limit,
            offset=offset
        )
        return messages
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}"
        )
