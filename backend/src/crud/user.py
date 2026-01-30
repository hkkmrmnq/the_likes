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
):
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
