from async_lru import alru_cache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, contains_eager, joinedload

from src.config.config import CFG
from src.db.core import Aspect, Attitude, UniqueValue, Value
from src.db.translations import AspectTranslation, ValueTranslation


async def read_values(
    *, user_language: str = CFG.DEFAULT_LANGUAGE, asession: AsyncSession
) -> list[Value]:
    if user_language == CFG.DEFAULT_LANGUAGE:
        stmt = select(Value).options(joinedload(Value.aspects))
    else:
        vt_trans = aliased(ValueTranslation)
        asp_trans = aliased(AspectTranslation)

        stmt = (
            select(Value)
            .join(vt_trans, Value.translations)
            .join(Value.aspects)
            .join(asp_trans, Aspect.translations)
            .options(
                contains_eager(Value.translations, alias=vt_trans),
                contains_eager(Value.aspects).contains_eager(
                    Aspect.translations, alias=asp_trans
                ),
            )
            .where(
                vt_trans.language_code == user_language,
                asp_trans.language_code == user_language,
            )
        )
    results = await asession.scalars(stmt)
    return list(results.unique().all())


async def read_attitudes(
    *, user_language: str = CFG.DEFAULT_LANGUAGE, asession: AsyncSession
) -> list[Attitude]:
    stmt = select(Attitude)
    if user_language != CFG.DEFAULT_LANGUAGE:
        stmt = stmt.options(joinedload(Attitude.translations))
    result = await asession.scalars(stmt)
    return list(result.unique().all())


@alru_cache
async def read_unique_values(
    *,
    asession: AsyncSession,
) -> list[UniqueValue]:
    result = await asession.scalars(select(UniqueValue))
    return list(result.all())
