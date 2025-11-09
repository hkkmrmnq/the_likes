from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from src.config.config import CFG
from src.crud.core import read_unique_values
from src.db.core import Aspect, Value
from src.db.personal_values import PersonalAspect, PersonalValue
from src.db.translations import AspectTranslation, ValueTranslation
from src.exceptions.exceptions import ServerError


async def get_uniquevalue_id_by_value_id_and_aspect_ids(
    *,
    value_id: int,
    aspect_ids: list[int],
    asession: AsyncSession,
) -> int:
    uvs = await read_unique_values(asession=asession)
    sorted_aspect_ids = set(aspect_ids)
    if not uvs:
        raise ServerError('UniqueValues not found.')
    for uv in uvs:
        if uv.value_id == value_id and set(uv.aspect_ids) == sorted_aspect_ids:
            return uv.id
    raise ServerError(
        f'UniqueValue not fount for {value_id=}, aspect_ids={aspect_ids}'
    )


async def read_personal_values(
    *,
    user_id: UUID,
    current_language: str = CFG.DEFAULT_LANGUAGE,
    asession: AsyncSession,
) -> list[PersonalValue]:
    stmt = (
        select(PersonalValue)
        .join(PersonalValue.value)
        .join(PersonalAspect)
        .join(Aspect)
        .where(PersonalValue.user_id == user_id)
    )
    if current_language in CFG.TRANSLATE_TO:
        stmt = (
            stmt.outerjoin(Value.translations)
            .outerjoin(Aspect.translations)
            .where(ValueTranslation.language_code == current_language)
            .where(AspectTranslation.language_code == current_language)
        )
    stmt = stmt.order_by(PersonalValue.user_order)
    if current_language in CFG.TRANSLATE_TO:
        stmt = stmt.options(
            contains_eager(PersonalValue.value).contains_eager(
                Value.translations
            ),
            contains_eager(PersonalValue.personal_aspects)
            .contains_eager(PersonalAspect.aspect)
            .contains_eager(Aspect.translations),
        )
    else:
        stmt = stmt.options(
            contains_eager(PersonalValue.value),
            contains_eager(PersonalValue.personal_aspects).contains_eager(
                PersonalAspect.aspect
            ),
        )
    db_personal_values_result = await asession.scalars(stmt)
    personal_values = list(db_personal_values_result.unique())
    return personal_values


async def count_personal_values(
    *, user_id: UUID, asession: AsyncSession
) -> int:
    result = await asession.scalar(
        select(func.count())
        .select_from(PersonalValue)
        .where(PersonalValue.user_id == user_id)
    )
    return result if result is not None else 0


async def create_personal_values(
    *,
    user_id: UUID,
    data: dict,
    asession: AsyncSession,
) -> list[PersonalValue]:
    personal_values = []
    for pv_data in data['value_links']:
        personal_value = PersonalValue(
            user_id=user_id,
            value_id=pv_data['value_id'],
            polarity=pv_data['polarity'],
            user_order=pv_data['user_order'],
        )
        personal_value.personal_aspects = [
            PersonalAspect(
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
                asession=asession,
            )
        )
        personal_values.append(personal_value)
    asession.add_all(personal_values)
    return personal_values


async def delete_personal_values(
    *,
    user_id: UUID,
    asession: AsyncSession,
) -> None:
    await asession.execute(
        delete(PersonalValue).where(PersonalValue.user_id == user_id)
    )
