from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

# User schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_online: bool
    last_seen: datetime
    
    class Config:
        from_attributes = True

# Chat schemas
class ChatType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"

class ChatCreate(BaseModel):
    title: str
    type: ChatType = ChatType.PRIVATE
    member_ids: List[int] = []

class ChatResponse(BaseModel):
    id: int
    title: str
    type: ChatType
    avatar_url: Optional[str] = None
    owner_id: int
    created_at: datetime
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0
    
    class Config:
        from_attributes = True

# Message schemas
class MessageStatus(str, Enum):
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class MessageCreate(BaseModel):
    chat_id: int
    content: str
    content_type: str = "text"
    reply_to_id: Optional[int] = None

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    sender_name: str
    content: str
    content_type: str
    status: MessageStatus
    reply_to_id: Optional[int] = None
    reply_to_content: Optional[str] = None
    created_at: datetime
    is_edited: bool
    
    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None
