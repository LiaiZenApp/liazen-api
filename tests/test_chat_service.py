"""
Test coverage for app/services/chat_service.py

This module provides comprehensive test coverage for the chat service.
"""
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime

from app.services.chat_service import send_message, get_messages, messages_store
from app.models.schemas import MessageDTO


pytestmark = pytest.mark.asyncio


class TestChatServiceSpecificLineCoverage:
    """Test specific uncovered lines in chat service."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Clear messages store before each test."""
        messages_store.clear()
    
    async def test_send_message_missing_sender_id_line_37(self):
        """Test line 37: raise ValueError when sender_id is missing."""
        with pytest.raises(ValueError, match="Both sender_id and recipient_id are required"):
            await send_message("", "recipient123", "test message")
    
    async def test_send_message_missing_recipient_id_line_37(self):
        """Test line 37: raise ValueError when recipient_id is missing."""
        with pytest.raises(ValueError, match="Both sender_id and recipient_id are required"):
            await send_message("sender123", "", "test message")
    
    async def test_send_message_self_message_line_42_43(self):
        """Test lines 42-43: raise ValueError when sending message to self."""
        with pytest.raises(ValueError, match="Cannot send message to yourself"):
            await send_message("user123", "user123", "test message")
    
    async def test_send_message_success_flow_lines_45_68(self):
        """Test lines 45-68: successful message creation and storage."""
        sender_id = "sender123"
        recipient_id = "recipient456"
        content = "Hello, world!"
        
        result = await send_message(sender_id, recipient_id, content)
        
        # Verify message creation
        assert isinstance(result, MessageDTO)
        assert result.sender_id == sender_id
        assert result.recipient_id == recipient_id
        assert result.content == content
        assert result.id is not None
        assert result.created_at is not None
        
        # Verify storage
        key = tuple(sorted([sender_id, recipient_id]))
        assert key in messages_store
        assert len(messages_store[key]) == 1
        assert messages_store[key][0] == result
    
    @patch('app.services.chat_service.logger')
    async def test_send_message_logging_line_63(self, mock_logger):
        """Test line 63: info logging on successful message send."""
        sender_id = "sender123"
        recipient_id = "recipient456"
        
        await send_message(sender_id, recipient_id, "test message")
        
        mock_logger.info.assert_called_once_with(f"Message sent from {sender_id} to {recipient_id}")
    
    @patch('app.services.chat_service.MessageDTO')
    async def test_send_message_exception_handling_lines_66_68(self, mock_message_dto):
        """Test lines 66-68: exception handling in send_message."""
        mock_message_dto.side_effect = Exception("Database error")
        
        with pytest.raises(ValueError, match="Failed to send message: Database error"):
            await send_message("sender123", "recipient456", "test message")
    
    @patch('app.services.chat_service.logger')
    @patch('app.services.chat_service.MessageDTO')
    async def test_send_message_error_logging_line_67(self, mock_message_dto, mock_logger):
        """Test line 67: error logging on exception."""
        mock_message_dto.side_effect = Exception("Database error")
        
        with pytest.raises(ValueError):
            await send_message("sender123", "recipient456", "test message")
        
        mock_logger.error.assert_called_once_with("Failed to send message: Database error")
    
    async def test_get_messages_missing_user_id_line_91_92(self):
        """Test lines 91-92: raise ValueError when user_id is missing."""
        with pytest.raises(ValueError, match="Both user_id and recipient_id are required"):
            await get_messages("", "recipient123")
    
    async def test_get_messages_missing_recipient_id_line_91_92(self):
        """Test lines 91-92: raise ValueError when recipient_id is missing."""
        with pytest.raises(ValueError, match="Both user_id and recipient_id are required"):
            await get_messages("user123", "")
    
    async def test_get_messages_invalid_limit_low_line_94_95(self):
        """Test lines 94-95: raise ValueError when limit is too low."""
        with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
            await get_messages("user123", "recipient456", limit=0)
    
    async def test_get_messages_invalid_limit_high_line_94_95(self):
        """Test lines 94-95: raise ValueError when limit is too high."""
        with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
            await get_messages("user123", "recipient456", limit=101)
    
    async def test_get_messages_negative_offset_line_97_98(self):
        """Test lines 97-98: raise ValueError when offset is negative."""
        with pytest.raises(ValueError, match="Offset cannot be negative"):
            await get_messages("user123", "recipient456", offset=-1)
    
    async def test_get_messages_success_flow_lines_100_118(self):
        """Test lines 100-118: successful message retrieval with sorting and pagination."""
        user_id = "user123"
        recipient_id = "recipient456"
        
        # Create test messages with different timestamps
        message1 = MessageDTO(
            id=uuid4(),
            sender_id=user_id,
            recipient_id=recipient_id,
            content="First message",
            created_at=datetime(2023, 1, 1, 10, 0, 0)
        )
        message2 = MessageDTO(
            id=uuid4(),
            sender_id=recipient_id,
            recipient_id=user_id,
            content="Second message",
            created_at=datetime(2023, 1, 1, 11, 0, 0)
        )
        message3 = MessageDTO(
            id=uuid4(),
            sender_id=user_id,
            recipient_id=recipient_id,
            content="Third message",
            created_at=datetime(2023, 1, 1, 12, 0, 0)
        )
        
        # Store messages
        key = tuple(sorted([user_id, recipient_id]))
        messages_store[key] = [message1, message2, message3]
        
        # Test retrieval with pagination
        result = await get_messages(user_id, recipient_id, limit=2, offset=0)
        
        # Verify sorting (newest first) and pagination
        assert len(result) == 2
        assert result[0] == message3  # Newest first
        assert result[1] == message2
        
        # Test offset
        result_offset = await get_messages(user_id, recipient_id, limit=2, offset=1)
        assert len(result_offset) == 2
        assert result_offset[0] == message2
        assert result_offset[1] == message1
    
    @patch('app.services.chat_service.logger')
    async def test_get_messages_logging_line_117(self, mock_logger):
        """Test line 117: info logging on successful message retrieval."""
        user_id = "user123"
        recipient_id = "recipient456"
        
        result = await get_messages(user_id, recipient_id)
        
        mock_logger.info.assert_called_once_with(f"Retrieved {len(result)} messages for user {user_id}")
    
    async def test_get_messages_empty_conversation_line_105(self):
        """Test line 105: handling empty conversation."""
        result = await get_messages("user123", "recipient456")
        assert result == []
    
    @patch('app.services.chat_service.sorted')
    async def test_get_messages_exception_handling_lines_120_122(self, mock_sorted):
        """Test lines 120-122: exception handling in get_messages."""
        mock_sorted.side_effect = Exception("Sorting error")
        
        with pytest.raises(ValueError, match="Failed to retrieve messages: Sorting error"):
            await get_messages("user123", "recipient456")
    
    @patch('app.services.chat_service.logger')
    @patch('app.services.chat_service.sorted')
    async def test_get_messages_error_logging_line_121(self, mock_sorted, mock_logger):
        """Test line 121: error logging on exception."""
        mock_sorted.side_effect = Exception("Sorting error")
        
        with pytest.raises(ValueError):
            await get_messages("user123", "recipient456")
        
        mock_logger.error.assert_called_once_with("Failed to retrieve messages: Sorting error")


class TestChatServiceEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Clear messages store before each test."""
        messages_store.clear()
    
    async def test_send_message_empty_content_after_strip(self):
        """Test sending message with only whitespace content."""
        with pytest.raises(ValueError, match="Message content cannot be empty"):
            await send_message("sender123", "recipient456", "   ")
    
    async def test_send_message_with_metadata(self):
        """Test sending message with metadata (parameter exists but not used)."""
        result = await send_message("sender123", "recipient456", "test", metadata={"key": "value"})
        assert result.content == "test"
    
    async def test_get_messages_exact_limit_boundaries(self):
        """Test get_messages with exact boundary values."""
        # Test minimum valid limit
        result = await get_messages("user123", "recipient456", limit=1)
        assert isinstance(result, list)
        
        # Test maximum valid limit
        result = await get_messages("user123", "recipient456", limit=100)
        assert isinstance(result, list)
    
    async def test_get_messages_zero_offset(self):
        """Test get_messages with zero offset."""
        result = await get_messages("user123", "recipient456", offset=0)
        assert isinstance(result, list)
    
    async def test_conversation_key_consistency(self):
        """Test that conversation key is consistent regardless of parameter order."""
        # Send message from A to B
        await send_message("userA", "userB", "message1")
        
        # Send message from B to A
        await send_message("userB", "userA", "message2")
        
        # Both should be in the same conversation
        messages_a = await get_messages("userA", "userB")
        messages_b = await get_messages("userB", "userA")
        
        assert len(messages_a) == 2
        assert len(messages_b) == 2
        assert messages_a == messages_b


class TestChatServiceBackwardCompatibility:
    """Test backward compatibility aliases."""
    
    async def test_backward_compatibility_aliases(self):
        """Test that backward compatibility aliases exist and work."""
        from app.services.chat_service import get_messages_service, send_message_service
        
        # Test that aliases point to the correct functions
        assert get_messages_service == get_messages
        assert send_message_service == send_message
        
        # Test that aliases work
        result = await send_message_service("sender123", "recipient456", "test message")
        assert isinstance(result, MessageDTO)
        
        messages = await get_messages_service("sender123", "recipient456")
        assert len(messages) == 1
        assert messages[0] == result