# api/users.py
from uuid import UUID
from fastapi import APIRouter, Query, Path, UploadFile, File, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional, List

from app.models.schemas import User, UserCreate, UserUpdate, UserCred, UserDeviceDTO
from app.services.user_service import (
    get_all_users,
    get_user_by_id,
    register_user,
    update_user,
    delete_user,
    update_password as update_user_password,
    upload_profile_image as upload_user_profile_image,
    register_device as register_user_device
)

router = APIRouter(tags=['Users'])
auth_scheme = HTTPBearer()

@router.get("", response_model=List[User])
async def list_users():
    """
    Get all users.
    
    Returns:
        List of User objects
    """
    try:
        return await get_all_users()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: UUID):
    """
    Get a user by ID.
    
    Args:
        user_id: UUID of the user to retrieve
        
    Returns:
        User object if found
    """
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """
    Register a new user.
    
    Args:
        user: User creation data
        
    Returns:
        Newly created User object
    """
    try:
        return await register_user(user)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )

@router.put("/{user_id}", response_model=User)
async def update_user_profile(
    user_id: UUID,
    user_update: UserUpdate,
    token: str = Depends(auth_scheme)
):
    """
    Update a user's profile information.
    
    Args:
        user_id: UUID of the user to update
        user_update: Fields to update
        token: JWT token for authentication
        
    Returns:
        Updated User object
    """
    try:
        return await update_user(user_id, user_update)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.put("/{user_id}/password", status_code=status.HTTP_200_OK)
async def update_password(
    user_id: UUID,
    creds: UserCred,
    token: str = Depends(auth_scheme)
):
    """
    Update a user's password.
    
    Args:
        user_id: UUID of the user
        creds: Current and new password
        token: JWT token for authentication
        
    Returns:
        Success message
    """
    try:
        return await update_user_password(creds)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update password: {str(e)}"
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(
    user_id: UUID,
    token: str = Depends(auth_scheme)
):
    """
    Delete a user account.
    
    Args:
        user_id: UUID of the user to delete
        token: JWT token for authentication
    """
    try:
        result = await delete_user(user_id)
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

@router.post("/{user_id}/profile-image", status_code=status.HTTP_200_OK)
async def upload_profile_image(
    user_id: UUID,
    file: UploadFile = File(...),
    token: str = Depends(auth_scheme)
):
    """
    Upload a profile image for a user.
    
    Args:
        user_id: UUID of the user
        file: Image file to upload
        token: JWT token for authentication
        
    Returns:
        Upload status and file path
    """
    try:
        return await upload_user_profile_image(user_id, file)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile image: {str(e)}"
        )

@router.post("/devices/register", status_code=status.HTTP_201_CREATED)
async def register_device(
    device: UserDeviceDTO,
    token: str = Depends(auth_scheme)
):
    """
    Register a user's device for push notifications.
    
    Args:
        device: Device information
        token: JWT token for authentication
        
    Returns:
        Registration status and device ID
    """
    try:
        return await register_user_device(device)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register device: {str(e)}"
        )
