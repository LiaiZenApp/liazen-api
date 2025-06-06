"""
Profile Service

This module provides services for managing user profiles.
"""
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import HTTPException, status, UploadFile
import aiofiles
import os

from app.models.schemas import ProfileCreate, ProfileUpdate, ProfileResponse
from app.core.config import settings

# In-memory storage for demonstration purposes
# In a real application, this would be a database
db_profiles: Dict[str, Dict] = {}


async def create_profile(profile_data: ProfileCreate) -> Dict[str, Any]:
    """
    Create a new user profile
    
    Args:
        profile_data: Profile data to create
        
    Returns:
        The created profile
        
    Raises:
        HTTPException: If a profile already exists for the user
    """
    # Check if profile already exists for this user
    existing_profile = next(
        (p for p in db_profiles.values() if p["user_id"] == str(profile_data.user_id)),
        None
    )
    
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists for this user"
        )
    
    # Create new profile
    profile_id = str(uuid4())
    now = datetime.utcnow()
    
    profile = {
        "id": profile_id,
        "user_id": str(profile_data.user_id),
        "bio": profile_data.bio,
        "location": profile_data.location,
        "website": str(profile_data.website) if profile_data.website else None,
        "birth_date": profile_data.birth_date.isoformat() if profile_data.birth_date else None,
        "gender": profile_data.gender,
        "profile_picture_url": str(profile_data.profile_picture_url) if profile_data.profile_picture_url else None,
        "cover_photo_url": str(profile_data.cover_photo_url) if profile_data.cover_photo_url else None,
        "phone_number": profile_data.phone_number,
        "preferred_language": profile_data.preferred_language or "en",
        "timezone": profile_data.timezone or "UTC",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    db_profiles[profile_id] = profile
    return profile


async def get_profile_by_user_id(user_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get a profile by user ID
    
    Args:
        user_id: ID of the user
        
    Returns:
        The profile if found, None otherwise
    """
    return next(
        (p for p in db_profiles.values() if p["user_id"] == str(user_id)),
        None
    )


async def get_profile(profile_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get a profile by its ID
    
    Args:
        profile_id: ID of the profile
        
    Returns:
        The profile if found, None otherwise
    """
    return db_profiles.get(str(profile_id))


async def update_profile(
    profile_id: UUID, 
    profile_data: ProfileUpdate,
    current_user_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Update a profile
    
    Args:
        profile_id: ID of the profile to update
        profile_data: Updated profile data
        current_user_id: ID of the current user (for authorization)
        
    Returns:
        The updated profile if found and authorized, None otherwise
        
    Raises:
        HTTPException: If profile not found or user not authorized
    """
    profile = await get_profile(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Check if the current user is the owner of the profile
    if profile["user_id"] != str(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile"
        )
    
    # Update only the fields that are provided in the update data
    update_data = profile_data.model_dump(exclude_unset=True)
    
    # Convert HttpUrl to string for storage
    if "website" in update_data and update_data["website"]:
        update_data["website"] = str(update_data["website"])
    if "profile_picture_url" in update_data and update_data["profile_picture_url"]:
        update_data["profile_picture_url"] = str(update_data["profile_picture_url"])
    if "cover_photo_url" in update_data and update_data["cover_photo_url"]:
        update_data["cover_photo_url"] = str(update_data["cover_photo_url"])
    
    # Update the profile
    updated_profile = {**profile, **update_data}
    updated_profile["updated_at"] = datetime.utcnow().isoformat()
    
    db_profiles[str(profile_id)] = updated_profile
    return updated_profile


async def upload_profile_picture(
    user_id: UUID,
    file: UploadFile,
    current_user_id: UUID
) -> Dict[str, str]:
    """
    Upload a profile picture
    
    Args:
        user_id: ID of the user
        file: The image file to upload
        current_user_id: ID of the current user (for authorization)
        
    Returns:
        Dictionary containing the URL of the uploaded image
        
    Raises:
        HTTPException: If upload fails or user not authorized
    """
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile"
        )
    
    # In a real application, you would upload the file to a storage service (e.g., S3, Azure Blob Storage)
    # For this example, we'll just save it locally
    
    # Create uploads directory if it doesn't exist
    upload_dir = os.path.join(settings.BASE_DIR, "uploads", "profile_pictures")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    try:
        # Save the file
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # In a real app, you would return the URL from your CDN/storage service
        file_url = f"/uploads/profile_pictures/{filename}"
        
        # Update the user's profile with the new picture URL
        profile = await get_profile_by_user_id(user_id)
        if profile:
            await update_profile(
                profile_id=UUID(profile["id"]),
                profile_data=ProfileUpdate(profile_picture_url=file_url),
                current_user_id=current_user_id
            )
        
        return {"url": file_url}
    except Exception as e:
        # Clean up the file if there was an error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )


# Add some test profiles for demonstration
if not db_profiles:
    from datetime import date, datetime
    
    test_profiles = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "user_id": "00000000-0000-0000-0000-000000000000",
            "bio": "Software engineer and tech enthusiast",
            "location": "San Francisco, CA",
            "website": "https://example.com/johndoe",
            "birth_date": date(1990, 1, 1).isoformat(),
            "gender": "Male",
            "profile_picture_url": "/uploads/profile_pictures/default.jpg",
            "cover_photo_url": "/uploads/cover_photos/default.jpg",
            "phone_number": "+1234567890",
            "preferred_language": "en",
            "timezone": "America/Los_Angeles",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    for profile in test_profiles:
        db_profiles[profile["id"]] = profile
