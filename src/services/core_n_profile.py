from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud
from .. import schemas as sch
from ..context import set_current_language
from ..exceptions import exceptions as exc
from ..models.core import Attitude, ValueTitle
from ..models.user_profile import Profile, User


async def is_active_verified(user: User) -> None:
    if not user.is_active:
        raise exc.InactiveUser
    if not user.is_verified:
        raise exc.UnverifiedUser


async def read_definitions(
    user: User, lan_code: str, session: AsyncSession
) -> Sequence[ValueTitle]:
    await is_active_verified(user)
    set_current_language(lan_code)
    definitions = await crud.read_definitions(lan_code, session)
    return definitions


async def read_attitudes(
    user: User, lan_code: str, session: AsyncSession
) -> Sequence[Attitude]:
    await is_active_verified(user)
    set_current_language(lan_code)
    attitudes = await crud.read_attitudes(lan_code, session)
    return attitudes


async def create_profile(
    user: User,
    session: AsyncSession,
) -> None:
    await crud.create_profile(user, session)
    await session.commit()


async def read_profile(
    user: User,
    lan_code: str,
    session: AsyncSession,
) -> Profile:
    await is_active_verified(user)
    profile = await crud.read_profile_by_user(user, lan_code, session)
    return profile


async def update_profile(
    user: User, lan_code: str, schema: sch.ProfileUpdate, session: AsyncSession
) -> Profile | None:
    await is_active_verified(user)
    profile = await crud.read_profile_by_user(user, lan_code, session)
    data = schema.model_dump(exclude={'longitude', 'latitude'})
    if all(
        (
            'distance_limit' in data,
            'location' not in data,
            profile.location is None,
        )
    ):
        raise exc.IncorrectBodyStructure(
            'Location unset - it is required for distance_limit.'
        )
    await crud.update_profile(user, data, session)
    await session.commit()
    await session.refresh(profile)
    return profile
