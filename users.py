from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from main import async_session
from models import User
from schemas import UserResponse
from dependencies import get_current_user, get_db
from auth import get_user_by_id, get_user_by_username, set_user_online_status

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def search_users(
    query: str = "",
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search users by username or display name."""
    result = await db.execute(
        select(User)
        .where(User.username.contains(query) | User.display_name.contains(query))
        .limit(20)
    )
    users = result.scalars().all()
    
    return users


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's full info."""
    user = await get_user_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID."""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/me")
async def update_profile(
    display_name: Optional[str] = None,
    bio: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    user = await get_user_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if display_name:
        user.display_name = display_name
    if bio:
        user.bio = bio
    
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    return {"message": "Profile updated successfully", "user": user}


@router.post("/online")
async def set_online_status(
    is_online: bool,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set user's online status."""
    await set_user_online_status(db, current_user["user_id"], is_online)
    return {"message": "Status updated"}
