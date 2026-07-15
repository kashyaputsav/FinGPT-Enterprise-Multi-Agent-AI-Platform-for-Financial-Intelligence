import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotAuthenticatedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise NotAuthenticatedError("Invalid token type")
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise NotAuthenticatedError("Invalid authentication credentials") from exc

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise NotAuthenticatedError("User not found or inactive")
    return user


def require_role(*allowed_roles: str):
    """Dependency factory for role-gated endpoints, e.g. compliance-only routes."""

    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles and user.role != "admin":
            from app.core.exceptions import PermissionDeniedError

            raise PermissionDeniedError(f"Requires one of roles: {allowed_roles}")
        return user

    return _checker
