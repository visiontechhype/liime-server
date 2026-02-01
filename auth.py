from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import User
from settings import Config
import hashlib
import secrets
import logging

logger = logging.getLogger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, stored_hash = hashed_password.split(':')
        computed_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
        return secrets.compare_digest(computed_hash, stored_hash)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password."""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}:{hash_obj.hexdigest()}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt


async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def authenticate_user(session: AsyncSession, username: str, password: str) -> Optional[User]:
    user = await get_user_by_username(session, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(session: AsyncSession, user_data) -> User:
    from pydantic import BaseModel
    
    class UserCreate(BaseModel):
        username: str
        email: str
        password: str
        display_name: str
    
    if isinstance(user_data, dict):
        user_data = UserCreate(**user_data)
    
    hashed_password = get_password_hash(user_data.password)
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        display_name=user_data.display_name,
        is_online=True,
        last_seen=datetime.utcnow()
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    logger.info(f"Created user: {user.username}")
    return user


async def update_user_last_seen(session: AsyncSession, user_id: int):
    user = await get_user_by_id(session, user_id)
    if user:
        user.last_seen = datetime.utcnow()
        await session.commit()


async def set_user_online_status(session: AsyncSession, user_id: int, is_online: bool):
    user = await get_user_by_id(session, user_id)
    if user:
        user.is_online = is_online
        if not is_online:
            user.last_seen = datetime.utcnow()
        await session.commit()
