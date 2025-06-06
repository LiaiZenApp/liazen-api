"""User service for handling user-related operations."""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
import logging
from fastapi import HTTPException, status, UploadFile, File, Depends
from datetime import datetime
import shutil
import os

from app.models.schemas import (
    User, 
    UserCreate, 
    UserUpdate, 
    UserDeviceDTO, 
    TokenResponse,
    UserCred,
    BaseUser
)
from app.core.security import get_password_hash, verify_password

# Configure logging
logger = logging.getLogger(__name__)

# In-memory storage for demo purposes
users_db: Dict[UUID, User] = {}
devices_db: Dict[UUID, UserDeviceDTO] = {}

# Directory for profile images
PROFILE_IMAGES_DIR = "profile_images"
os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)

# Mock database functions for demo purposes
async def get_all_users() -> List[User]:
    """Get all users."""
    return list(users_db.values())

async def get_user_by_id(user_id: UUID) -> Optional[User]:
    """Get a user by ID."""
    return users_db.get(user_id)

async def get_user_by_email(email: str) -> Optional[User]:
    """Get a user by email."""
    for user in users_db.values():
        if user.email == email:
            return user
    return None

async def register_user(user_create: UserCreate) -> User:
    """Register a new user."""
    # Check if user already exists
    existing_user = await get_user_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = uuid4()
    hashed_password = get_password_hash(user_create.password)
    user = User(
        id=user_id,
        email=user_create.email,
        hashed_password=hashed_password,
        first_name=user_create.first_name,
        last_name=user_create.last_name,
        is_active=user_create.is_active,
        is_verified=user_create.is_verified,
        role=user_create.role,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Save to database (in-memory for demo)
    users_db[user_id] = user
    logger.info(f"Registered new user: {user.email}")
    return user

async def update_user(user_id: UUID, user_update: UserUpdate) -> User:
    """Update a user's information."""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    update_data = user_update.model_dump(exclude_unset=True)

    
    # Handle password update
    if 'password' in update_data and update_data['password']:
        update_data['hashed_password'] = get_password_hash(update_data.pop('password'))
    
    # Update user fields
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    users_db[user_id] = user
    logger.info(f"Updated user: {user.email}")
    return user

async def delete_user(user_id: UUID) -> Dict[str, Any]:
    """Delete a user by ID."""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # In a real app, you might want to soft delete
    del users_db[user_id]
    logger.info(f"Deleted user: {user.email}")
    return {"success": True, "message": "User deleted successfully"}

async def update_password(creds: UserCred) -> Dict[str, Any]:
    """Update a user's password."""
    user = await get_user_by_email(creds.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    user.hashed_password = get_password_hash(creds.new_password)
    user.updated_at = datetime.utcnow()
    users_db[user.id] = user
    
    logger.info(f"Updated password for user: {user.email}")
    return {"success": True, "message": "Password updated successfully"}

async def upload_profile_image(
    user_id: UUID, 
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """Upload a profile image for a user."""
    # Verify user exists
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create unique filename
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{user_id}{file_extension}"
    file_path = os.path.join(PROFILE_IMAGES_DIR, filename)
    
    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Error saving profile image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save profile image"
        )
    
    # In a real app, save the file path to the user record
    logger.info(f"Uploaded profile image for user: {user.email}")
    return {
        "success": True, 
        "message": "Profile image uploaded successfully",
        "file_path": file_path
    }

async def register_device(device: UserDeviceDTO) -> Dict[str, Any]:
    """Register a user's device for push notifications."""
    # Verify user exists
    user = await get_user_by_id(device.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if device already registered
    for existing_device in devices_db.values():
        if existing_device.device_id == device.device_id:
            # Update existing device
            existing_device.device_type = device.device_type
            existing_device.device_name = device.device_name
            existing_device.os_version = device.os_version
            existing_device.app_version = device.app_version
            existing_device.last_used = datetime.utcnow()
            existing_device.is_active = True
            
            logger.info(f"Updated device registration for user: {user.email}")
            return {
                "success": True,
                "message": "Device registration updated",
                "device_id": existing_device.id
            }
    
    # Register new device
    device_id = uuid4()
    device.id = device_id
    device.created_at = datetime.utcnow()
    device.last_used = datetime.utcnow()
    device.is_active = True
    
    devices_db[device_id] = device
    
    logger.info(f"Registered new device for user: {user.email}")
    return {
        "success": True,
        "message": "Device registered successfully",
        "device_id": device_id
    }