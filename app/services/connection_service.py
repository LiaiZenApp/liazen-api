"""
LiaiZen API - Connection Service Module

This module provides comprehensive services for managing user connections and relationships
within the LiaiZen social networking platform. It handles the creation, retrieval, updating,
and deletion of connections between users.

Key Features:
- User connection management (friend requests, connections)
- Connection status tracking (pending, accepted, rejected, blocked)
- Bidirectional relationship handling
- Authorization checks for connection operations
- Search and filtering capabilities
- In-memory storage with database-ready architecture

Business Logic:
- Users cannot connect to themselves
- Duplicate connections are prevented
- Only target users can accept/reject connection requests
- Both parties can delete connections
- Status transitions follow business rules

Architecture:
- Service layer pattern for business logic separation
- DTO (Data Transfer Object) pattern for data consistency
- Repository pattern ready for database integration
- Comprehensive error handling with HTTP status codes

Author: LiaiZen Development Team
Version: 1.0
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import HTTPException, status
from app.models.schemas import ConnectionDTO, ConnectionCreate, ConnectionStatus

# ============================================================================
# DATA STORAGE
# ============================================================================

# In-memory storage for demonstration purposes
# In production, this would be replaced with a database repository
# This design allows for easy migration to PostgreSQL/SQLAlchemy later
connections_db: List[ConnectionDTO] = []

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _find_connection(connection_id: str) -> Optional[ConnectionDTO]:
    """
    Helper function to find a connection by its unique identifier.
    
    This function searches through the in-memory connections database
    to locate a specific connection. In a production environment,
    this would be replaced with a database query.
    
    Args:
        connection_id (str): The unique identifier of the connection
        
    Returns:
        Optional[ConnectionDTO]: The connection if found, None otherwise
        
    Note:
        Uses string comparison to handle both UUID and string inputs
        for maximum compatibility with different ID formats.
    """
    for conn in connections_db:
        if str(conn.id) == str(connection_id):
            return conn
    return None


# ============================================================================
# CORE SERVICE FUNCTIONS
# ============================================================================

async def create_connection(
    user_id: str,
    target_user_id: str,
    status: str = "pending"
) -> ConnectionDTO:
    """
    Create a new connection between two users.
    
    This function handles the creation of a new connection request between users.
    It implements business rules to prevent invalid connections and ensures
    data integrity by checking for existing connections.
    
    Business Rules:
    - Users cannot connect to themselves
    - Duplicate connections are not allowed
    - Default status is "pending" for new connection requests
    - Bidirectional relationship checking (A->B or B->A)
    
    Args:
        user_id (str): ID of the user initiating the connection request
        target_user_id (str): ID of the user being invited to connect
        status (str, optional): Initial status of the connection. Defaults to "pending"
        
    Returns:
        ConnectionDTO: The newly created connection object with all metadata
        
    Raises:
        ValueError: If user tries to connect to themselves
        ValueError: If a connection already exists between the users
        
    Example:
        >>> connection = await create_connection("user123", "user456")
        >>> print(connection.status)  # "pending"
        
    Note:
        In production, this would include database transaction handling
        and potentially trigger notification events to the target user.
    """
    # Validate business rule: users cannot connect to themselves
    if user_id == target_user_id:
        raise ValueError("Cannot connect to yourself")
    
    # Check for existing connection in either direction (bidirectional)
    # This prevents duplicate connections regardless of who initiated
    existing = next(
        (c for c in connections_db
         if {str(c.user_id), str(c.target_user_id)} == {user_id, target_user_id}),
        None
    )
    
    if existing:
        raise ValueError("Connection already exists")
    
    # Create new connection with generated UUID and timestamps
    connection = ConnectionDTO(
        id=uuid4(),  # Generate unique identifier
        user_id=UUID(user_id),  # Convert to UUID for type safety
        target_user_id=UUID(target_user_id),
        status=status,
        created_at=datetime.utcnow(),  # Track creation time
        updated_at=datetime.utcnow()   # Track last modification
    )
    
    # Store in database (in-memory for demo)
    connections_db.append(connection)
    
    # TODO: In production, add notification logic here
    # - Send push notification to target user
    # - Create activity log entry
    # - Update user connection counts
    
    return connection


async def get_connections(
    user_id: str,
    status: Optional[str] = None,
    **kwargs  # Accept additional kwargs for backward compatibility
) -> List[ConnectionDTO]:
    """
    Get all connections for a user
    
    Args:
        user_id: ID of the user
        status: Optional status filter
        
    Returns:
        List[ConnectionDTO]: List of connections
    """
    # Filter connections where user is either user_id or target_user_id
    connections = [
        c for c in connections_db 
        if str(c.user_id) == str(user_id) or str(c.target_user_id) == str(user_id)
    ]
    
    # Apply status filter if provided
    if status is not None:
        connections = [c for c in connections if c.status == status]
    
    return connections


async def get_connection(connection_id: str) -> ConnectionDTO:
    """
    Get a specific connection by ID
    
    Args:
        connection_id: ID of the connection
        
    Returns:
        ConnectionDTO: The connection if found
        
    Raises:
        HTTPException: If connection not found
    """
    connection = _find_connection(str(connection_id))
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    return connection


async def update_connection_status(
    connection_id: str,
    new_status: str,
    user_id: str
) -> ConnectionDTO:
    """
    Update the status of a connection
    
    Args:
        connection_id: ID of the connection
        new_status: New status (e.g., 'accepted', 'rejected')
        user_id: ID of the user making the request
        
    Returns:
        ConnectionDTO: Updated connection
        
    Raises:
        HTTPException: If connection not found or update is invalid
    """
    connection = _find_connection(str(connection_id))
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Verify the user is part of this connection
    user_id_str = str(user_id)
    connection_user_id_str = str(connection.user_id)
    target_user_id_str = str(connection.target_user_id)
    
    print(f"Debug - User ID: {user_id_str}, Type: {type(user_id)}")
    print(f"Debug - Connection User ID: {connection_user_id_str}, Type: {type(connection.user_id)}")
    print(f"Debug - Target User ID: {target_user_id_str}, Type: {type(connection.target_user_id)}")
    print(f"Debug - Comparing {user_id_str} with [{connection_user_id_str}, {target_user_id_str}]")
    
    if user_id_str not in [connection_user_id_str, target_user_id_str]:
        print("Debug - Raising 403 Forbidden: User is not part of this connection")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this connection"
        )
    
    # Only allow updating to valid statuses
    valid_statuses = [s.value for s in ConnectionStatus]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Only the target user can accept/reject a connection
    if new_status in [ConnectionStatus.ACCEPTED, ConnectionStatus.REJECTED] and str(connection.target_user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the target user can accept or reject a connection"
        )
    
    # Update the status and timestamp
    connection.status = new_status
    connection.updated_at = datetime.utcnow()
    
    return connection


async def delete_connection(connection_id: str, user_id: str) -> Dict[str, str]:
    """
    Delete a connection
    
    Args:
        connection_id: ID of the connection to delete
        user_id: ID of the user making the request
        
    Returns:
        Dict: Confirmation message
        
    Raises:
        HTTPException: If connection not found or user not authorized
    """
    connection = _find_connection(str(connection_id))
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Verify the user is part of this connection
    if str(user_id) not in [str(connection.user_id), str(connection.target_user_id)]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this connection"
        )
    
    # Remove the connection
    connections_db.remove(connection)
    return {"message": "Connection deleted successfully"}


async def search_connections(
    user_id: str,
    query: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> List[ConnectionDTO]:
    """
    Search for connections with optional filters
    
    Args:
        user_id: ID of the user
        query: Optional search query string (not implemented)
        status: Optional status filter
        limit: Maximum number of results to return
        offset: Number of results to skip
        
    Returns:
        List[ConnectionDTO]: List of matching connections
    """
    # Get user's connections
    connections = await get_connections(user_id=user_id)
    
    # Apply status filter if provided
    if status is not None:
        connections = [c for c in connections if c.status == status]
    
    # Apply pagination
    return connections[offset:offset + limit]


# For backward compatibility with tests
get_connections_svc = get_connections
update_connection_svc = update_connection_status
delete_connection_svc = delete_connection
create_connection_svc = create_connection
