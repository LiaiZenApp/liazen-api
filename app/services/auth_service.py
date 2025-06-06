# app/services/auth_service.py

import requests
from fastapi import HTTPException, status
from app.models.schemas import UserCred, TokenResponse
from app.core.config import settings
from app.core.security import decode_jwt


def login_user(credentials: UserCred) -> TokenResponse:
    """
    Authenticate user using Auth0's /oauth/token endpoint.
    """
    payload = {
        "grant_type": "password",
        "username": credentials.username,
        "password": credentials.password,
        "audience": settings.AUTH0_AUDIENCE,
        "client_id": settings.AUTH0_CLIENT_ID,
        "client_secret": settings.AUTH0_CLIENT_SECRET,
    }

    try:
        response = requests.post(f"https://{settings.AUTH0_DOMAIN}/oauth/token", json=payload)
    except (requests.exceptions.RequestException, TimeoutError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication service unavailable: {str(e)}"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or Auth0 failure"
        )

    data = response.json()

    access_token = data["access_token"]
    decoded = decode_jwt(access_token)
    sub = decoded.get("sub", "auth0-user")

    return TokenResponse(
        access_token=access_token,
        refresh_token=data.get("refresh_token"),
        expires_in=data["expires_in"],
        uniqueId=sub
    )


def refresh_token(data: TokenResponse) -> TokenResponse:
    """
    Use refresh_token to get new access_token via Auth0.
    """
    payload = {
        "grant_type": "refresh_token",
        "client_id": settings.AUTH0_CLIENT_ID,
        "client_secret": settings.AUTH0_CLIENT_SECRET,
        "refresh_token": data.refresh_token
    }

    try:
        response = requests.post(f"https://{settings.AUTH0_DOMAIN}/oauth/token", json=payload)
    except (requests.exceptions.RequestException, TimeoutError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh service unavailable: {str(e)}"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Get the new tokens from the response
    token_data = response.json()
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token", data.refresh_token)
    expires_in = token_data["expires_in"]
    token_type = token_data.get("token_type", "Bearer")
    
    # Decode the new access token to get the user ID
    decoded = decode_jwt(access_token)
    sub = decoded.get("sub", "auth0-user")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        token_type=token_type,
        uniqueId=sub
    )
