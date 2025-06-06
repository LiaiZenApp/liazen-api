from fastapi import APIRouter, Path, Query, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
from app.models.schemas import EventDTO, EventCreate, EventUpdate
from app.services.event_service import (
    create_event,
    get_events_by_user,
    get_event_by_id,
    delete_event
)

router = APIRouter(prefix='/api/events', tags=['Events'])
auth_scheme = HTTPBearer()

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_event_endpoint(
    event: EventCreate,
    token: str = Depends(auth_scheme)
) -> dict:
    """
    Create a new event.
    
    - **event**: Event data to create
    - **token**: JWT token for authentication
    """
    try:
        return await create_event(event)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}"
        )

@router.get("/user/{user_id}", response_model=dict)
async def get_user_events(
    user_id: int = Path(..., description="ID of the user to fetch events for"),
    search_text: Optional[str] = Query(None, description="Optional search text to filter events"),
    time_zone: Optional[str] = Query(None, description="Optional timezone for time conversion"),
    token: str = Depends(auth_scheme)
) -> dict:
    """
    Get events for a specific user with optional filtering.
    
    - **user_id**: ID of the user
    - **search_text**: Optional text to search in event titles/descriptions
    - **time_zone**: Optional timezone for time conversion
    - **token**: JWT token for authentication
    """
    try:
        return await get_events_by_user(user_id, search_text, time_zone)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user events: {str(e)}"
        )

@router.get("/{event_id}", response_model=dict)
async def get_event(
    event_id: int = Path(..., description="ID of the event to retrieve"),
    token: str = Depends(auth_scheme)
) -> dict:
    """
    Get a specific event by its ID.
    
    - **event_id**: ID of the event to retrieve
    - **token**: JWT token for authentication
    """
    try:
        return await get_event_by_id(event_id)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch event: {str(e)}"
        )

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_endpoint(
    event_id: int = Path(..., description="ID of the event to delete"),
    token: str = Depends(auth_scheme)
) -> None:
    """
    Delete an event by its ID.
    
    - **event_id**: ID of the event to delete
    - **token**: JWT token for authentication
    """
    try:
        result = await delete_event(event_id)
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found"
            )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete event: {str(e)}"
        )
