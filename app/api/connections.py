"""
LiaiZen API - Connections API Module

This module provides comprehensive REST API endpoints for managing user connections
and relationships within the LiaiZen social networking platform.

Key Features:
- Create connection requests between users
- Retrieve user connections with filtering options
- Update connection status (accept, reject, block)
- Delete connections with proper authorization
- Comprehensive error handling and validation
- Dependency injection for testability

API Endpoints:
- POST /connections - Create a new connection request
- GET /connections - Retrieve user's connections with optional filtering
- PATCH /connections/{id} - Update connection status
- DELETE /connections/{id} - Delete a connection

Security:
- All endpoints require JWT authentication
- Authorization checks ensure users can only manage their own connections
- Input validation prevents invalid operations
- Proper HTTP status codes for different scenarios

Architecture:
- Service layer pattern for business logic separation
- Dependency injection for service functions (testability)
- Comprehensive error handling with appropriate HTTP responses
- Type-safe request/response models with Pydantic

Author: LiaiZen Development Team
Version: 1.0
"""

from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer

from app.models.schemas import User, ConnectionDTO, ConnectionCreate
from app.services.connection_service import (
    create_connection as create_connection_svc,
    get_connections as get_connections_svc,
    update_connection_status as update_connection_svc,
    delete_connection as delete_connection_svc
)
from app.core.security import get_current_user

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_connection_service():
    """
    Dependency injection for connection service functions.
    
    This function provides a dictionary of service functions that can be
    easily mocked during testing. It follows the dependency injection pattern
    to improve testability and maintainability.
    
    Returns:
        dict: Dictionary containing all connection service functions
        
    Note:
        This pattern allows for easy mocking in tests by overriding
        the dependency with test implementations.
    """
    return {
        'create_connection': create_connection_svc,
        'get_connections': get_connections_svc,
        'update_connection_status': update_connection_svc,
        'delete_connection': delete_connection_svc
    }

# ============================================================================
# ROUTER CONFIGURATION
# ============================================================================

router = APIRouter(tags=['Connections'])
security = HTTPBearer()

@router.post("", response_model=ConnectionDTO, status_code=status.HTTP_201_CREATED)
async def create_connection(
    connection_data: ConnectionCreate,
    current_user: User = Depends(get_current_user),
    services: dict = Depends(get_connection_service)
) -> ConnectionDTO:
    """
    Create a new connection between the current user and another user
    
    Args:
        connection_data: Connection creation data
        current_user: The authenticated user
        
    Returns:
        The created connection details
        
    Raises:
        HTTPException: With appropriate status code and detail message
    """
    print(f"DEBUG: create_connection called with {connection_data=}, {current_user=}")
    
    # Check if current user is active
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive users cannot create connections"
        )
        
    # Check if target user is the same as current user
    if str(connection_data.target_user_id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create connection to yourself"
        )
    
    try:
        # Convert target_user_id to string if it's a UUID object
        target_user_id = str(connection_data.target_user_id)
        print(f"DEBUG: Converted target_user_id to {target_user_id}")
        
        print(f"DEBUG: Calling create_connection with user_id={current_user.id}, target_user_id={target_user_id}")
        result = await services['create_connection'](
            user_id=str(current_user.id),
            target_user_id=target_user_id,
            status=connection_data.status or "pending"
        )
        print(f"DEBUG: create_connection_svc returned {result}")
        return result
    except ValueError as e:
        print(f"DEBUG: ValueError in create_connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException as he:
        print(f"DEBUG: HTTPException in create_connection: {str(he)}")
        raise he
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"DEBUG: Unexpected error in create_connection: {str(e)}\n{tb}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create connection: {str(e)}"
        )

@router.get("", response_model=List[ConnectionDTO])
async def get_connections(
    connection_status: str = None,
    current_user: User = Depends(get_current_user),
    services: dict = Depends(get_connection_service)
):
    """
    Get all connections for the current user
    
    Args:
        connection_status: Optional status filter (e.g., 'pending', 'accepted', 'rejected')
        current_user: The authenticated user
        
    Returns:
        List[ConnectionDTO]: List of connections
    """
    try:
        return await services['get_connections'](
            user_id=str(current_user.id),
            status=connection_status
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve connections: {str(e)}"
        )



@router.patch("/{connection_id}", response_model=ConnectionDTO)
async def update_connection(
    connection_id: str,
    new_status: str = Query(..., alias="status"),
    current_user: User = Depends(get_current_user),
    services: dict = Depends(get_connection_service)
):
    """
    Update the status of a connection
    
    Args:
        connection_id: ID of the connection to update
        new_status: New status (e.g., 'accepted', 'rejected')
        current_user: The authenticated user
        
    Returns:
        ConnectionDTO: Updated connection
    """
    try:
        return await services['update_connection_status'](
            connection_id=connection_id,
            new_status=new_status,
            user_id=str(current_user.id)
        )
    except HTTPException as he:
        # Re-raise HTTP exceptions as they are
        raise he
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update connection: {str(e)}"
        )

@router.delete("/{connection_id}", status_code=status.HTTP_200_OK)
async def delete_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    services: dict = Depends(get_connection_service)
):
    """
    Delete a connection
    
    Args:
        connection_id: ID of the connection to delete
        current_user: The authenticated user (injected dependency)
        
    Returns:
        Dict with a success message
        
    Raises:
        HTTPException: With appropriate status code and detail message
    """
    try:
        # Validate that connection_id is a valid UUID
        try:
            from uuid import UUID
            UUID(connection_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid UUID format"
            )
            
        return await services['delete_connection'](
            connection_id=connection_id,
            user_id=str(current_user.id)
        )
    except HTTPException as he:
        # Re-raise the HTTPException to preserve the original status code and detail
        raise he from None
    except Exception as e:
        # Log the error for debugging
        import logging
        logging.error(f"Error deleting connection {connection_id}: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete connection: {str(e)}"
        )
