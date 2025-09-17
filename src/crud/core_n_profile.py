from typing import Sequence

from async_lru import alru_cache
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .. import constants as cnst
from .. import models as md
from ..exceptions import exceptions as exc


def create_profile(
    user: md.User,
    session: AsyncSession,
) -> None:
    session.add(md.Profile(user_id=user.id))


async def read_profile_by_user(
    user: md.User, lan_code: str, session: AsyncSession
) -> md.Profile:
    options = joinedload(md.Profile.attitude)
    if lan_code != cnst.LANGUAGE_DEFAULT:
        options = options.joinedload(md.Attitude.translations)
    stmt = (
        select(md.Profile)
        .options(options)
        .where(md.Profile.user_id == user.id)
    )
    profile = await session.scalar(stmt)
    if profile is None:
        raise exc.ServerError(f'Profile not found for user_id {user.id}')
    return profile


async def read_profile_by_id(
    profile_id: int, session: AsyncSession
) -> md.Profile:
    profile = await session.scalar(
        select(md.Profile)
        .options(joinedload(md.Profile.attitude))
        .where(md.Profile.id == profile_id)
    )
    if profile is None:
        raise exc.ServerError('Profile not found.')
    return profile


async def update_profile(
    user: md.User,
    data: dict,
    session: AsyncSession,
) -> None:
    stmt = (
        update(md.Profile).where(md.Profile.user_id == user.id).values(**data)
    )
    await session.execute(stmt)


async def read_definitions(
    lan_code: str, session: AsyncSession
) -> list[md.ValueTitle]:
    if lan_code == cnst.LANGUAGE_DEFAULT:
        stmt = select(md.ValueTitle).options(joinedload(md.ValueTitle.aspects))
    else:
        stmt = select(md.ValueTitle).options(
            joinedload(md.ValueTitle.translations),
            joinedload(md.ValueTitle.aspects).joinedload(
                md.Aspect.translations
            ),
        )
    result = await session.scalars(stmt)
    definitions = list(result.unique().all())
    if not definitions:
        raise exc.ServerError('Definitions not found.')
    return definitions


async def read_attitudes(
    lan_code: str, session: AsyncSession
) -> list[md.Attitude]:
    stmt = select(md.Attitude)
    if lan_code != cnst.LANGUAGE_DEFAULT:
        stmt = stmt.options(joinedload(md.Attitude.translations))
    result = await session.scalars(stmt)
    attitudes = list(result.unique().all())
    if not attitudes:
        raise exc.ServerError('Attitudes not found.')
    return attitudes


@alru_cache
async def read_unique_values(
    session: AsyncSession,
) -> Sequence[md.UniqueValue]:
    result = await session.scalars(select(md.UniqueValue))
    return result.all()


@alru_cache
async def get_mapped_uvs(session: AsyncSession) -> dict[tuple, int]:
    uvs = await read_unique_values(session)
    mapped_uvs = {tuple(sorted(uv.aspect_ids)): uv.id for uv in uvs}
    return mapped_uvs


async def get_unique_value_id_by_aspect_ids(
    aspect_ids: list[int],
    session: AsyncSession,
) -> int:
    mapped_uvs = await get_mapped_uvs(session)
    return mapped_uvs[tuple(sorted(aspect_ids))]
