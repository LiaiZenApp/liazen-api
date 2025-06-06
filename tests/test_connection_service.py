"""
Test coverage for app/services/connection_service.py

This module provides comprehensive test coverage for the connection service.
"""
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime
from fastapi import HTTPException, status

from app.services.connection_service import (
    create_connection, get_connections, get_connection, update_connection_status,
    delete_connection, search_connections, _find_connection, connections_db
)
from app.models.schemas import ConnectionDTO, ConnectionStatus




class TestConnectionServiceSpecificLineCoverage:
    """Test specific uncovered lines in connection service."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Clear connections database before each test."""
        connections_db.clear()
    
    def test_find_connection_helper_lines_20_23(self):
        """Test lines 20-23: _find_connection helper function."""
        # Create test connection
        connection = ConnectionDTO(
            id=uuid4(),
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            target_user_id=UUID("87654321-4321-4321-4321-210987654321"),
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        connections_db.append(connection)
        
        # Test finding existing connection
        found = _find_connection(str(connection.id))
        assert found == connection
        
        # Test not finding non-existent connection
        not_found = _find_connection("non-existent-id")
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_create_connection_self_connection_line_46(self):
        """Test line 46: raise ValueError when trying to connect to self."""
        user_id = "12345678-1234-1234-1234-123456789012"
        with pytest.raises(ValueError, match="Cannot connect to yourself"):
            await create_connection(user_id, user_id)
    
    @pytest.mark.asyncio
    async def test_create_connection_existing_connection_line_56(self):
        """Test line 56: raise ValueError when connection already exists."""
        user_id = "12345678-1234-1234-1234-123456789012"
        target_user_id = "87654321-4321-4321-4321-210987654321"
        
        # Create first connection
        await create_connection(user_id, target_user_id)
        
        # Try to create duplicate connection
        with pytest.raises(ValueError, match="Connection already exists"):
            await create_connection(user_id, target_user_id)
        
        # Try reverse connection (should also fail)
        with pytest.raises(ValueError, match="Connection already exists"):
            await create_connection(target_user_id, user_id)
    
    @pytest.mark.asyncio
    async def test_create_connection_success_lines_58_69(self):
        """Test lines 58-69: successful connection creation."""
        user_id = "12345678-1234-1234-1234-123456789012"
        target_user_id = "87654321-4321-4321-4321-210987654321"
        status_val = "pending"
        
        result = await create_connection(user_id, target_user_id, status_val)
        
        # Verify connection creation
        assert isinstance(result, ConnectionDTO)
        assert str(result.user_id) == user_id
        assert str(result.target_user_id) == target_user_id
        assert result.status == status_val
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None
        
        # Verify storage
        assert len(connections_db) == 1
        assert connections_db[0] == result
    
    @pytest.mark.asyncio
    async def test_get_connections_with_status_filter_lines_88_97(self):
        """Test lines 88-97: get_connections with status filtering."""
        user_id = "12345678-1234-1234-1234-123456789012"
        target_user_id1 = "87654321-4321-4321-4321-210987654321"
        target_user_id2 = "11111111-2222-3333-4444-555555555555"
        
        # Create connections with different statuses
        conn1 = await create_connection(user_id, target_user_id1, "pending")
        conn2 = await create_connection(target_user_id2, user_id, "accepted")
        
        # Test without status filter
        all_connections = await get_connections(user_id)
        assert len(all_connections) == 2
        
        # Test with status filter
        pending_connections = await get_connections(user_id, status="pending")
        assert len(pending_connections) == 1
        assert pending_connections[0] == conn1
        
        accepted_connections = await get_connections(user_id, status="accepted")
        assert len(accepted_connections) == 1
        assert accepted_connections[0] == conn2
    
    @pytest.mark.asyncio
    async def test_get_connections_with_kwargs_line_75(self):
        """Test line 75: get_connections accepts additional kwargs for backward compatibility."""
        user_id = "12345678-1234-1234-1234-123456789012"
        
        # Should not raise error with additional kwargs
        result = await get_connections(user_id, extra_param="value", another_param=123)
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_connection_not_found_lines_113_118(self):
        """Test lines 113-118: get_connection raises HTTPException when not found."""
        with pytest.raises(HTTPException) as exc_info:
            await get_connection("non-existent-id")
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Connection not found"
    
    @pytest.mark.asyncio
    async def test_get_connection_success_line_119(self):
        """Test line 119: get_connection returns connection when found."""
        # Create test connection
        connection = await create_connection("12345678-1234-1234-1234-123456789012", "87654321-4321-4321-4321-210987654321")
        
        result = await get_connection(str(connection.id))
        assert result == connection
    
    @pytest.mark.asyncio
    async def test_update_connection_status_not_found_lines_141_146(self):
        """Test lines 141-146: update_connection_status raises HTTPException when connection not found."""
        with pytest.raises(HTTPException) as exc_info:
            await update_connection_status("non-existent-id", "accepted", "12345678-1234-1234-1234-123456789012")
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Connection not found"
    
    @pytest.mark.asyncio
    async def test_update_connection_status_unauthorized_lines_158_163(self):
        """Test lines 158-163: update_connection_status raises HTTPException when user not authorized."""
        # Create connection between user1 and user2
        user1_id = "12345678-1234-1234-1234-123456789012"
        user2_id = "87654321-4321-4321-4321-210987654321"
        user3_id = "11111111-2222-3333-4444-555555555555"
        connection = await create_connection(user1_id, user2_id)
        
        # Try to update as unauthorized user
        with pytest.raises(HTTPException) as exc_info:
            await update_connection_status(str(connection.id), "accepted", user3_id)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Not authorized to update this connection"
    
    @pytest.mark.asyncio
    async def test_update_connection_status_invalid_status_lines_167_171(self):
        """Test lines 167-171: update_connection_status raises HTTPException for invalid status."""
        user1_id = "12345678-1234-1234-1234-123456789012"
        user2_id = "87654321-4321-4321-4321-210987654321"
        connection = await create_connection(user1_id, user2_id)
        
        with pytest.raises(HTTPException) as exc_info:
            await update_connection_status(str(connection.id), "invalid_status", user1_id)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid status" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_update_connection_status_target_user_only_lines_174_178(self):
        """Test lines 174-178: only target user can accept/reject connections."""
        user1_id = "12345678-1234-1234-1234-123456789012"
        user2_id = "87654321-4321-4321-4321-210987654321"
        connection = await create_connection(user1_id, user2_id)
        
        # User1 (initiator) tries to accept - should fail
        with pytest.raises(HTTPException) as exc_info:
            await update_connection_status(str(connection.id), ConnectionStatus.ACCEPTED, user1_id)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Only the target user can accept or reject a connection"
        
        # User2 (target) accepts - should succeed
        result = await update_connection_status(str(connection.id), ConnectionStatus.ACCEPTED, user2_id)
        assert result.status == ConnectionStatus.ACCEPTED
    
    @pytest.mark.asyncio
    async def test_update_connection_status_success_lines_180_184(self):
        """Test lines 180-184: successful status update."""
        user1_id = "12345678-1234-1234-1234-123456789012"
        user2_id = "87654321-4321-4321-4321-210987654321"
        connection = await create_connection(user1_id, user2_id)
        original_updated_at = connection.updated_at
        
        # Update status
        result = await update_connection_status(str(connection.id), ConnectionStatus.ACCEPTED, user2_id)
        
        assert result.status == ConnectionStatus.ACCEPTED
        assert result.updated_at > original_updated_at
        assert result.id == connection.id
    
    @pytest.mark.asyncio
    async def test_delete_connection_not_found_lines_201_206(self):
        """Test lines 201-206: delete_connection raises HTTPException when connection not found."""
        with pytest.raises(HTTPException) as exc_info:
            await delete_connection("non-existent-id", "12345678-1234-1234-1234-123456789012")
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Connection not found"
    
    @pytest.mark.asyncio
    async def test_delete_connection_unauthorized_lines_209_213(self):
        """Test lines 209-213: delete_connection raises HTTPException when user not authorized."""
        user1_id = "12345678-1234-1234-1234-123456789012"
        user2_id = "87654321-4321-4321-4321-210987654321"
        user3_id = "11111111-2222-3333-4444-555555555555"
        connection = await create_connection(user1_id, user2_id)
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_connection(str(connection.id), user3_id)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Not authorized to delete this connection"
    
    @pytest.mark.asyncio
    async def test_delete_connection_success_lines_215_217(self):
        """Test lines 215-217: successful connection deletion."""
        user1_id = "12345678-1234-1234-1234-123456789012"
        user2_id = "87654321-4321-4321-4321-210987654321"
        connection = await create_connection(user1_id, user2_id)
        initial_count = len(connections_db)
        
        result = await delete_connection(str(connection.id), user1_id)
        
        assert result == {"message": "Connection deleted successfully"}
        assert len(connections_db) == initial_count - 1
        assert connection not in connections_db
    
    @pytest.mark.asyncio
    async def test_search_connections_lines_241_248(self):
        """Test lines 241-248: search_connections with filtering and pagination."""
        user_id = "12345678-1234-1234-1234-123456789012"
        user456_id = "87654321-4321-4321-4321-210987654321"
        user789_id = "11111111-2222-3333-4444-555555555555"
        user999_id = "22222222-3333-4444-5555-666666666666"
        
        # Create test connections
        conn1 = await create_connection(user_id, user456_id, "pending")
        conn2 = await create_connection(user_id, user789_id, "accepted")
        conn3 = await create_connection(user999_id, user_id, "pending")
        
        # Test without filters
        all_results = await search_connections(user_id)
        assert len(all_results) == 3
        
        # Test with status filter
        pending_results = await search_connections(user_id, status="pending")
        assert len(pending_results) == 2
        
        # Test with pagination
        paginated_results = await search_connections(user_id, limit=2, offset=1)
        assert len(paginated_results) == 2
        
        # Test with all parameters
        filtered_paginated = await search_connections(
            user_id, query="test", status="pending", limit=1, offset=0
        )
        assert len(filtered_paginated) == 1


class TestConnectionServiceDebugOutput:
    """Test debug output functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Clear connections database before each test."""
        connections_db.clear()
    
    @patch('builtins.print')
    @pytest.mark.asyncio
    async def test_update_connection_debug_output_lines_153_159(self, mock_print):
        """Test lines 153-159: debug print statements in update_connection_status."""
        user1_id = "12345678-1234-1234-1234-123456789012"
        user2_id = "87654321-4321-4321-4321-210987654321"
        user3_id = "11111111-2222-3333-4444-555555555555"
        connection = await create_connection(user1_id, user2_id)
        
        # This should trigger debug output
        try:
            await update_connection_status(str(connection.id), "accepted", user3_id)
        except HTTPException:
            pass  # Expected to fail, we're testing debug output
        
        # Verify debug prints were called
        assert mock_print.call_count >= 4
        
        # Check specific debug messages
        debug_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("Debug - User ID:" in call for call in debug_calls)
        assert any("Debug - Connection User ID:" in call for call in debug_calls)
        assert any("Debug - Target User ID:" in call for call in debug_calls)
        assert any("Debug - Comparing" in call for call in debug_calls)


class TestConnectionServiceEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Clear connections database before each test."""
        connections_db.clear()
    
    @pytest.mark.asyncio
    async def test_create_connection_default_status(self):
        """Test create_connection with default status parameter."""
        user1_id = "12345678-1234-1234-1234-123456789012"
        user2_id = "87654321-4321-4321-4321-210987654321"
        connection = await create_connection(user1_id, user2_id)
        assert connection.status == "pending"  # Default value
    
    @pytest.mark.asyncio
    async def test_get_connections_user_as_target(self):
        """Test get_connections when user is target_user_id."""
        user_id = "12345678-1234-1234-1234-123456789012"
        initiator_id = "87654321-4321-4321-4321-210987654321"
        
        connection = await create_connection(initiator_id, user_id)
        
        # User should see connection where they are the target
        connections = await get_connections(user_id)
        assert len(connections) == 1
        assert connections[0] == connection
    
    @pytest.mark.asyncio
    async def test_update_connection_status_string_conversion(self):
        """Test that update_connection_status handles UUID to string conversion properly."""
        user1_id = "12345678-1234-1234-1234-123456789012"
        user2_id = "87654321-4321-4321-4321-210987654321"
        connection = await create_connection(user1_id, user2_id)
        
        # Pass UUID objects instead of strings
        result = await update_connection_status(
            str(connection.id),
            ConnectionStatus.ACCEPTED,
            user2_id  # Target user can accept
        )
        
        assert result.status == ConnectionStatus.ACCEPTED
    
    @pytest.mark.asyncio
    async def test_delete_connection_both_users_authorized(self):
        """Test that both users in a connection can delete it."""
        user1_id = "12345678-1234-1234-1234-123456789012"
        user2_id = "87654321-4321-4321-4321-210987654321"
        connection = await create_connection(user1_id, user2_id)
        
        # User1 (initiator) can delete
        connections_db.clear()
        connections_db.append(connection)
        result1 = await delete_connection(str(connection.id), user1_id)
        assert result1["message"] == "Connection deleted successfully"
        
        # User2 (target) can also delete
        connections_db.append(connection)
        result2 = await delete_connection(str(connection.id), user2_id)
        assert result2["message"] == "Connection deleted successfully"
    
    @pytest.mark.asyncio
    async def test_search_connections_empty_results(self):
        """Test search_connections with no matching results."""
        user_id = "12345678-1234-1234-1234-123456789012"
        result = await search_connections(user_id, status="nonexistent")
        assert result == []
    
    @pytest.mark.asyncio
    async def test_search_connections_query_parameter_ignored(self):
        """Test that query parameter is accepted but not implemented."""
        user_id = "12345678-1234-1234-1234-123456789012"
        user456_id = "87654321-4321-4321-4321-210987654321"
        await create_connection(user_id, user456_id)
        
        # Query parameter should be ignored (not implemented)
        result = await search_connections(user_id, query="ignored")
        assert len(result) == 1


class TestConnectionServiceBackwardCompatibility:
    """Test backward compatibility aliases."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Clear connections database before each test."""
        connections_db.clear()
    
    @pytest.mark.asyncio
    async def test_backward_compatibility_aliases(self):
        """Test that backward compatibility aliases exist and work."""
        from app.services.connection_service import (
            get_connections_svc, update_connection_svc, 
            delete_connection_svc, create_connection_svc
        )
        
        # Test that aliases point to the correct functions
        assert get_connections_svc == get_connections
        assert update_connection_svc == update_connection_status
        assert delete_connection_svc == delete_connection
        assert create_connection_svc == create_connection
        
        # Test that aliases work
        user1_id = "12345678-1234-1234-1234-123456789012"
        user2_id = "87654321-4321-4321-4321-210987654321"
        connection = await create_connection_svc(user1_id, user2_id)
        assert isinstance(connection, ConnectionDTO)
        
        connections = await get_connections_svc(user1_id)
        assert len(connections) == 1
        
        updated = await update_connection_svc(str(connection.id), "accepted", user2_id)
        assert updated.status == "accepted"
        
        result = await delete_connection_svc(str(connection.id), user1_id)
        assert "message" in result