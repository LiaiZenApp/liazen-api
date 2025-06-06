"""
Profile API

This module provides API endpoints for managing user profiles.
"""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer

from app.models.schemas import ProfileCreate, ProfileUpdate, ProfileResponse
from app.services.profile_service import (
    create_profile as create_profile_svc,
    get_profile as get_profile_svc,
    get_profile_by_user_id as get_profile_by_user_id_svc,
    update_profile as update_profile_svc,
    upload_profile_picture as upload_profile_picture_svc
)
from app.core.security import get_current_user
from app.models.schemas import User

router = APIRouter(prefix="", tags=["Profiles"])
security = HTTPBearer()

@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's profile
    
    Args:
        current_user: The authenticated user (injected dependency)
        
    Returns:
        The user's profile
        
    Raises:
        HTTPException: If the profile is not found
    """
    profile = await get_profile_by_user_id_svc(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create a profile first."
        )
    return profile


@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update the current user's profile
    
    Args:
        profile_data: The updated profile data
        current_user: The authenticated user (injected dependency)
        
    Returns:
        The updated profile
        
    Raises:
        HTTPException: If the profile is not found or update fails
    """
    # Get the current profile to get its ID
    current_profile = await get_profile_by_user_id_svc(current_user.id)
    if not current_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create a profile first."
        )
    
    updated_profile = await update_profile_svc(
        profile_id=current_profile["id"],
        profile_data=profile_data,
        current_user_id=current_user.id
    )
    
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    return updated_profile


@router.post("/me/picture", status_code=status.HTTP_200_OK)
async def upload_my_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a profile picture for the current user
    
    Args:
        file: The image file to upload
        current_user: The authenticated user (injected dependency)
        
    Returns:
        Dictionary containing the URL of the uploaded image
        
    Raises:
        HTTPException: If upload fails or user not authorized
    """
    try:
        return await upload_profile_picture_svc(
            user_id=current_user.id,
            file=file,
            current_user_id=current_user.id
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_user_profile(
    user_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get a user's public profile
    
    Args:
        user_id: ID of the user whose profile to retrieve
        current_user: The authenticated user (injected dependency)
        
    Returns:
        The requested user's public profile
        
    Raises:
        HTTPException: If the profile is not found or access is denied
    """
    profile = await get_profile_by_user_id_svc(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # In a real app, you might want to return a different response
    # for the current user vs other users (e.g., include private fields)
    return profile


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProfileResponse)
async def create_user_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new profile for the current user
    
    Args:
        profile_data: The profile data
        current_user: The authenticated user (injected dependency)
        
    Returns:
        The created profile
        
    Raises:
        HTTPException: If a profile already exists or creation fails
    """
    # Ensure the user is creating a profile for themselves
    if str(profile_data.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a profile for another user"
        )
    
    try:
        return await create_profile_svc(profile_data)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}"
        )
