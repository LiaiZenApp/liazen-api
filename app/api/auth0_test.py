"""
Auth0 Test Endpoints

This module provides test endpoints to verify Auth0 integration.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import jwt

from app.core.security import auth0_scheme
from app.core.config import settings
from app.models.schemas import User

router = APIRouter(tags=["Auth0 Test"])
security = HTTPBearer()

@router.get("/public")
async def public_endpoint():
    """Public endpoint that doesn't require authentication"""
    return {
        "message": "This is a public endpoint. No authentication required.",
        "status": "success"
    }

@router.get("/protected")
async def protected_endpoint(current_user: User = Depends(auth0_scheme)):
    """Protected endpoint that requires a valid Auth0 token"""
    return {
        "message": "You have accessed a protected endpoint!",
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": getattr(current_user, 'name', None),
            "picture": getattr(current_user, 'picture', None)
        },
        "status": "success"
    }

@router.get("/metadata")
async def auth0_metadata():
    """Get Auth0 metadata for debugging"""
    return {
        "auth0_domain": settings.AUTH0_DOMAIN,
        "auth0_audience": settings.AUTH0_AUDIENCE,
        "auth0_issuer": settings.auth0_issuer,
        "auth0_jwks_uri": settings.auth0_jwks_uri,
        "auth0_authorization_url": settings.auth0_authorization_url,
        "auth0_token_url": settings.auth0_token_url,
        "auth0_userinfo_url": settings.auth0_userinfo_url,
    }
