from fastapi import APIRouter, Query, Path, Depends, HTTPException, status
from typing import Optional, Any, Dict
from app.models.schemas import MemberDTO, UserMemberDto
from app.services.member_service import (
    get_member,
    get_member_by_email,
    create_member,
    delete_member,
    get_relationships,
    invite_member
)
from app.core.security import get_current_user

router = APIRouter(prefix='/api/members', tags=['Members'])

@router.get("/{user_id}")
async def get_member_by_user_id(
    user_id: str = Path(..., description="User ID as UUID string"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        return get_member(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/email/{email}")
async def get_by_email(
    email: str = Path(..., description="Email address of the member"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        return get_member_by_email(email)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("", status_code=status.HTTP_201_CREATED)
async def create(
    member: MemberDTO,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        return create_member(member)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete(
    user_id: str = Path(..., description="User ID as UUID string"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        delete_member(user_id)
        return {"status": "success", "message": "Member deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/relationships/list")
async def relationships(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        return get_relationships()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/invite", status_code=status.HTTP_202_ACCEPTED)
async def invite(
    data: UserMemberDto,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        return invite_member(data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
