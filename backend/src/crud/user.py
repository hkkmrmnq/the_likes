from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src import db
from src.config import ENM


async def read_user_by_email(
    *, email: str, asession: AsyncSession
) -> db.User | None:
    return await asession.scalar(select(db.User).where(db.User.email == email))


async def read_user_by_id(
    *, user_id: UUID, asession: AsyncSession
) -> db.User | None:
    return await asession.scalar(select(db.User).where(db.User.id == user_id))


def create_user(
    *,
    email: str,
    hashed_password: str,
    is_superuser: bool = False,
    is_verified: bool = False,
    asession: AsyncSession,
) -> None:
    user = db.User(
        email=email,
        password_hash=hashed_password,
        is_superuser=is_superuser,
        is_verified=is_verified,
    )
    profile = db.Profile(user=user)
    user_dynamic = db.UserDynamic(
        user=user, search_allowed_status=ENM.SearchAllowedStatus.OK.value
    )
    asession.add_all((user, profile, user_dynamic))


async def get_all_valid_refresh_tokens_for_user(
    *, user_id: UUID, asession: AsyncSession
) -> list[db.RefreshToken]:
    stmt = select(db.RefreshToken).where(
        db.RefreshToken.user_id == user_id,
        db.RefreshToken.revoked_at.is_(None),
        db.RefreshToken.expires_at > datetime.now(timezone.utc),
    )
    results = await asession.execute(stmt)
    return list(results.scalars().all())


async def get_specific_refresh_token(
    jti: UUID, asession: AsyncSession
) -> db.RefreshToken | None:
    stmt = select(db.RefreshToken).where(db.RefreshToken.jti == jti)
    return await asession.scalar(stmt)
