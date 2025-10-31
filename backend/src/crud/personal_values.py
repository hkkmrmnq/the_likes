from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, func, orm, select
from sqlalchemy.ext.asyncio import AsyncSession

from src import db
from src import exceptions as exc
from src.config import CFG
from src.crud.core import read_unique_values


async def get_uniquevalue_id_by_value_id_and_aspect_ids(
    *,
    value_id: int,
    aspect_ids: list[int],
    a_session: AsyncSession,
) -> int:
    uvs = await read_unique_values(a_session=a_session)
    sorted_aspect_ids = set(aspect_ids)
    if not uvs:
        raise exc.ServerError('UniqueValues not found.')
    for uv in uvs:
        if uv.value_id == value_id and set(uv.aspect_ids) == sorted_aspect_ids:
            return uv.id
    raise exc.ServerError(
        f'UniqueValue not fount for {value_id=}, aspect_ids={aspect_ids}'
    )


async def read_personal_values(
    *, user_id: UUID, lan_code: str, a_session: AsyncSession
) -> Sequence[db.PersonalValue]:
    stmt = (
        select(db.PersonalValue)
        .join(db.Value)
        .outerjoin(db.PersonalAspect)
        .outerjoin(db.Aspect)
        .where(db.PersonalValue.user_id == user_id)
        .options(
            orm.joinedload(db.PersonalValue.value),
            orm.joinedload(db.PersonalValue.personal_aspects).joinedload(
                db.PersonalAspect.aspect
            ),
        )
    )
    if lan_code != CFG.DEFAULT_LANGUAGE:
        stmt = stmt.options(
            orm.joinedload(db.PersonalValue.value).joinedload(
                db.Value.translations
            ),
            orm.joinedload(db.PersonalValue.personal_aspects)
            .joinedload(db.PersonalAspect.aspect)
            .joinedload(db.Aspect.translations),
        )
    result = await a_session.scalars(stmt)
    profile_value_links = result.unique().all()
    return profile_value_links


async def count_personal_values(
    *, user_id: UUID, a_session: AsyncSession
) -> int:
    result = await a_session.scalar(
        select(func.count())
        .select_from(db.PersonalValue)
        .where(db.PersonalValue.user_id == user_id)
    )
    return result if result is not None else 0


async def create_personal_values(
    *,
    user_id: UUID,
    data: dict,
    a_session: AsyncSession,
) -> list[db.PersonalValue]:
    personal_values = []
    for pv_data in data['value_links']:
        personal_value = db.PersonalValue(
            user_id=user_id,
            value_id=pv_data['value_id'],
            polarity=pv_data['polarity'],
            user_order=pv_data['user_order'],
        )
        personal_value.personal_aspects = [
            db.PersonalAspect(
                user_id=user_id,
                aspect_id=aspect_data['aspect_id'],
                included=aspect_data['included'],
            )
            for aspect_data in pv_data['aspects']
        ]
        personal_value.unique_value_id = (
            await get_uniquevalue_id_by_value_id_and_aspect_ids(
                value_id=pv_data['value_id'],
                aspect_ids=[
                    a['aspect_id'] for a in pv_data['aspects'] if a['included']
                ],
                a_session=a_session,
            )
        )
        personal_values.append(personal_value)
    a_session.add_all(personal_values)
    return personal_values


async def delete_personal_values(
    *,
    user_id: UUID,
    a_session: AsyncSession,
) -> None:
    await a_session.execute(
        delete(db.PersonalValue).where(db.PersonalValue.user_id == user_id)
    )
