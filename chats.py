from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from main import async_session
from models import User, Chat, Message, ChatType
from schemas import ChatCreate, ChatResponse
from dependencies import get_current_user, get_db

router = APIRouter()


@router.get("/", response_model=List[ChatResponse])
async def get_chats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all chats for current user."""
    user_id = current_user["user_id"]
    
    # Get user's chats
    result = await db.execute(
        select(Chat)
        .options(selectinload(Chat.members), selectinload(Chat.messages))
        .where(Chat.members.any(id=user_id))
        .order_by(desc(Chat.updated_at))
    )
    chats = result.scalars().all()
    
    response = []
    for chat in chats:
        # Get last message
        last_msg = chat.messages[0] if chat.messages else None
        
        # Count unread messages (messages after last read)
        unread_result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat.id)
            .where(Message.sender_id != user_id)
            .where(Message.created_at > (current_user.get("last_seen", datetime.min)))
        )
        unread_count = len(unread_result.scalars().all())
        
        # Determine chat title
        if chat.type == ChatType.PRIVATE:
            # For private chats, show other member's name
            other_member = [m for m in chat.members if m.id != user_id]
            title = other_member[0].display_name if other_member else "Unknown"
        else:
            title = chat.title
        
        response.append({
            "id": chat.id,
            "title": title,
            "type": chat.type.value,
            "avatar_url": chat.avatar_url,
            "owner_id": chat.owner_id,
            "created_at": chat.created_at,
            "last_message": last_msg.content if last_msg else None,
            "last_message_time": last_msg.created_at if last_msg else None,
            "unread_count": unread_count
        })
    
    return response


@router.post("/", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat."""
    user_id = current_user["user_id"]
    
    chat = Chat(
        title=chat_data.title,
        type=ChatType(chat_data.type.value) if isinstance(chat_data.type, str) else chat_data.type,
        owner_id=user_id
    )
    
    # Add owner as member
    owner_result = await db.execute(select(User).where(User.id == user_id))
    owner = owner_result.scalar_one()
    chat.members.append(owner)
    
    # Add other members
    for member_id in chat_data.member_ids:
        member_result = await db.execute(select(User).where(User.id == member_id))
        member = member_result.scalar_one_or_none()
        if member:
            chat.members.append(member)
    
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    
    return {
        "id": chat.id,
        "title": chat.title,
        "type": chat.type.value,
        "avatar_url": chat.avatar_url,
        "owner_id": chat.owner_id,
        "created_at": chat.created_at,
        "last_message": None,
        "last_message_time": None,
        "unread_count": 0
    }


@router.get("/{chat_id}")
async def get_chat(
    chat_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat by ID."""
    user_id = current_user["user_id"]
    
    result = await db.execute(
        select(Chat)
        .options(selectinload(Chat.members))
        .where(Chat.id == chat_id)
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Check if user is member
    if user_id not in [m.id for m in chat.members]:
        raise HTTPException(status_code=403, detail="Not a member of this chat")
    
    return {
        "id": chat.id,
        "title": chat.title if chat.type != ChatType.PRIVATE else "Chat",
        "type": chat.type.value,
        "members": [{"id": m.id, "username": m.username, "display_name": m.display_name} for m in chat.members]
    }


@router.post("/{chat_id}/leave")
async def leave_chat(
    chat_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Leave a chat."""
    user_id = current_user["user_id"]
    
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id)
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    member = next((m for m in chat.members if m.id == user_id), None)
    if member:
        chat.members.remove(member)
        await db.commit()
    
    return {"message": "Left chat successfully"}
