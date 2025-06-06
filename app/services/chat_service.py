from datetime import datetime
from typing import List, Dict, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime
import logging

from app.models.schemas import MessageRequest, MessageDTO

# Set up logging
logger = logging.getLogger(__name__)

# In-memory storage for demo purposes
messages_store: Dict[Tuple[str, str], List[MessageDTO]] = {}

async def send_message(
    sender_id: str,
    recipient_id: str,
    content: str,
    metadata: Optional[dict] = None
) -> MessageDTO:
    """
    Send a message from one user to another.
    
    Args:
        sender_id: ID of the message sender (must be a string)
        recipient_id: ID of the message recipient (must be a string)
        content: Message content
        metadata: Optional metadata for the message
        
    Returns:
        MessageDTO: The created message
        
    Raises:
        ValueError: If validation fails
    """
    if not sender_id or not recipient_id:
        raise ValueError("Both sender_id and recipient_id are required")
        
    if not content or not content.strip():
        raise ValueError("Message content cannot be empty")
    
    if sender_id == recipient_id:
        raise ValueError("Cannot send message to yourself")
    
    try:
        # Create a new message
        message = MessageDTO(
            id=uuid4(),
            sender_id=str(sender_id),
            recipient_id=str(recipient_id),
            content=content,
            created_at=datetime.utcnow()
        )
        
        # Generate a consistent key for the conversation
        key = tuple(sorted([sender_id, recipient_id]))
        
        # Store the message
        if key not in messages_store:
            messages_store[key] = []
        messages_store[key].append(message)
        
        logger.info(f"Message sent from {sender_id} to {recipient_id}")
        return message
        
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        raise ValueError(f"Failed to send message: {str(e)}")

async def get_messages(
    user_id: str,
    recipient_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[MessageDTO]:
    """
    Get messages between two users.
    
    Args:
        user_id: ID of the current user (must be a string)
        recipient_id: ID of the other user (must be a string)
        limit: Maximum number of messages to return (1-100)
        offset: Number of messages to skip
        
    Returns:
        List[MessageDTO]: List of messages between the users, ordered by creation time (newest first)
        
    Raises:
        ValueError: If validation fails
    """
    if not user_id or not recipient_id:
        raise ValueError("Both user_id and recipient_id are required")
        
    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")
        
    if offset < 0:
        raise ValueError("Offset cannot be negative")
    
    try:
        # Generate the same key used for storage
        key = tuple(sorted([str(user_id), str(recipient_id)]))
        
        # Get messages for this conversation
        conversation = messages_store.get(key, [])
        
        # Sort by creation time (newest first)
        conversation_sorted = sorted(
            conversation, 
            key=lambda x: x.created_at, 
            reverse=True
        )
        
        # Apply pagination
        result = conversation_sorted[offset:offset + limit]
        
        logger.info(f"Retrieved {len(result)} messages for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to retrieve messages: {str(e)}")
        raise ValueError(f"Failed to retrieve messages: {str(e)}")

# For backward compatibility with tests
get_messages_service = get_messages
send_message_service = send_message