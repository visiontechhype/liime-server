from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from main import async_session
from models import User, Chat, Message, MessageStatus
from schemas import MessageCreate, MessageResponse
from dependencies import get_current_user, get_db

router = APIRouter()


@router.get("/{chat_id}", response_model=List[MessageResponse])
async def get_messages(
    chat_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages for a chat."""
    user_id = current_user["user_id"]
    
    # Verify chat exists and user is member
    chat_result = await db.execute(
        select(Chat).where(Chat.id == chat_id)
    )
    chat = chat_result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if user_id not in [m.id for m in chat.members]:
        raise HTTPException(status_code=403, detail="Not a member of this chat")
    
    # Get messages
    result = await db.execute(
        select(Message)
        .options(selectinload(Message.sender), selectinload(Message.reply_to))
        .where(Message.chat_id == chat_id)
        .order_by(desc(Message.created_at))
        .limit(limit)
        .offset(offset)
    )
    messages = result.scalars().all()
    
    response = []
    for msg in reversed(messages):  # Oldest first
        reply_content = None
        if msg.reply_to:
            reply_content = msg.reply_to.content[:50] + "..." if len(msg.reply_to.content) > 50 else msg.reply_to.content
        
        response.append({
            "id": msg.id,
            "chat_id": msg.chat_id,
            "sender_id": msg.sender_id,
            "sender_name": msg.sender.display_name,
            "content": msg.content,
            "content_type": msg.content_type,
            "status": msg.status.value if hasattr(msg.status, 'value') else str(msg.status),
            "reply_to_id": msg.reply_to_id,
            "reply_to_content": reply_content,
            "created_at": msg.created_at,
            "is_edited": msg.is_edited
        })
    
    return response


@router.post("/", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a new message."""
    user_id = current_user["user_id"]
    
    # Verify chat exists and user is member
    chat_result = await db.execute(
        select(Chat).where(Chat.id == message_data.chat_id)
    )
    chat = chat_result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if user_id not in [m.id for m in chat.members]:
        raise HTTPException(status_code=403, detail="Not a member of this chat")
    
    # Create message
    message = Message(
        chat_id=message_data.chat_id,
        sender_id=user_id,
        content=message_data.content,
        content_type=message_data.content_type,
        status=MessageStatus.SENT,
        reply_to_id=message_data.reply_to_id
    )
    
    db.add(message)
    
    # Update chat
    chat.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(message)
    await db.refresh(message.sender)
    await db.refresh(message.reply_to)
    
    reply_content = None
    if message.reply_to:
        reply_content = message.reply_to.content[:50] + "..." if len(message.reply_to.content) > 50 else message.reply_to.content
    
    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "sender_name": message.sender.display_name,
        "content": message.content,
        "content_type": message.content_type,
        "status": message.status.value if hasattr(message.status, 'value') else str(message.status),
        "reply_to_id": message.reply_to_id,
        "reply_to_content": reply_content,
        "created_at": message.created_at,
        "is_edited": message.is_edited
    }


@router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a message."""
    user_id = current_user["user_id"]
    
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Only sender can delete
    if message.sender_id != user_id:
        raise HTTPException(status_code=403, detail="Can only delete your own messages")
    
    await db.delete(message)
    await db.commit()
    
    return {"message": "Message deleted successfully"}


@router.put("/{message_id}", response_model=MessageResponse)
async def edit_message(
    message_id: int,
    new_content: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Edit a message."""
    user_id = current_user["user_id"]
    
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.sender_id != user_id:
        raise HTTPException(status_code=403, detail="Can only edit your own messages")
    
    # Can't edit messages older than 24 hours
    if (datetime.utcnow() - message.created_at).total_seconds() > 86400:
        raise HTTPException(status_code=400, detail="Cannot edit message older than 24 hours")
    
    message.content = new_content
    message.is_edited = True
    message.edited_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(message)
    await db.refresh(message.sender)
    
    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "sender_name": message.sender.display_name,
        "content": message.content,
        "content_type": message.content_type,
        "status": message.status.value if hasattr(message.status, 'value') else str(message.status),
        "reply_to_id": message.reply_to_id,
        "reply_to_content": None,
        "created_at": message.created_at,
        "is_edited": message.is_edited
    }
