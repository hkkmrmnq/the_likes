from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, func, orm, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import db as db
from ..config import constants as CNST
from ..services._utils import (
    get_uniquevalue_id_by_valuetitle_id_and_aspect_ids,
)


async def read_personal_values(
    *, user_id: UUID, lan_code: str, a_session: AsyncSession
) -> Sequence[db.PersonalValue]:
    stmt = (
        select(db.PersonalValue)
        .join(db.ValueTitle)
        .outerjoin(db.PersonalAspect)
        .outerjoin(db.Aspect)
        .where(db.PersonalValue.user_id == user_id)
        .options(
            orm.joinedload(db.PersonalValue.value_title),
            orm.joinedload(db.PersonalValue.personal_aspects).joinedload(
                db.PersonalAspect.aspect
            ),
        )
    )
    if lan_code != CNST.LANGUAGE_DEFAULT:
        stmt = stmt.options(
            orm.joinedload(db.PersonalValue.value_title).joinedload(
                db.ValueTitle.translations
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
            value_title_id=pv_data['value_title_id'],
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
            await get_uniquevalue_id_by_valuetitle_id_and_aspect_ids(
                value_title_id=pv_data['value_title_id'],
                aspect_ids=[a['aspect_id'] for a in pv_data['aspects']],
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
