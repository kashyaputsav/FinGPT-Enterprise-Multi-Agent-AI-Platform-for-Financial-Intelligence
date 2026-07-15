from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotAuthenticatedError, ValidationFailedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.schemas import UserCreate
from app.models.user import User


async def register_user(db: AsyncSession, payload: UserCreate) -> User:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise ValidationFailedError("A user with this email already exists")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.hashed_password):
        raise NotAuthenticatedError("Invalid email or password")
    if not user.is_active:
        raise NotAuthenticatedError("This account has been deactivated")
    return user


def issue_tokens(user: User) -> dict:
    return {
        "access_token": create_access_token(subject=str(user.id), extra_claims={"role": user.role}),
        "refresh_token": create_refresh_token(subject=str(user.id)),
        "token_type": "bearer",
    }
