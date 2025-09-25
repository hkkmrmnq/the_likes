from typing import Sequence

from async_lru import alru_cache
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .. import models as md
from .. import schemas as sch
from ..config import constants as CNST
from ..exceptions import exceptions as exc


async def create_profile(
    user: md.User,
    session: AsyncSession,
) -> None:
    session.add(md.Profile(user_id=user.id))


async def read_profile_by_user(
    user: md.User, lan_code: str, session: AsyncSession
) -> md.Profile:
    options = joinedload(md.Profile.attitude)
    if lan_code != CNST.LANGUAGE_DEFAULT:
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
    if lan_code == CNST.LANGUAGE_DEFAULT:
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
    if lan_code != CNST.LANGUAGE_DEFAULT:
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


async def get_unique_value_id_by_vt_id_and_aspect_ids(
    vl_schema: sch.ProfileValueLinkCreate,
    session: AsyncSession,
) -> int:
    aspect_ids = [al.aspect_id for al in vl_schema.aspects if al.included]
    uvs = await read_unique_values(session)
    for uv in uvs:
        if uv.value_title_id == vl_schema.value_title_id and sorted(
            uv.aspect_ids
        ) == sorted(aspect_ids):
            return uv.id
    raise exc.ServerError(
        (
            'Unique Values not fount for value_title_id='
            f'{vl_schema.value_title_id}, aspect_ids={aspect_ids}'
        )
    )
