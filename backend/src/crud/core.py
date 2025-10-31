from async_lru import alru_cache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, contains_eager, joinedload

from src import db
from src.config import CFG
from src.context import get_current_language


async def read_definitions(*, a_session: AsyncSession) -> list[db.Value]:
    user_language = get_current_language()
    if user_language == CFG.DEFAULT_LANGUAGE:
        stmt = select(db.Value).options(joinedload(db.Value.aspects))
    else:
        vt_trans = aliased(db.ValueTranslation)
        asp_trans = aliased(db.AspectTranslation)

        stmt = (
            select(db.Value)
            .join(vt_trans, db.Value.translations)
            .join(db.Value.aspects)
            .join(asp_trans, db.Aspect.translations)
            .options(
                contains_eager(db.Value.translations, alias=vt_trans),
                contains_eager(db.Value.aspects).contains_eager(
                    db.Aspect.translations, alias=asp_trans
                ),
            )
            .where(
                vt_trans.language_code == user_language,
                asp_trans.language_code == user_language,
            )
        )
    results = await a_session.scalars(stmt)
    return list(results.unique().all())


async def read_attitudes(*, a_session: AsyncSession) -> list[db.Attitude]:
    stmt = select(db.Attitude)
    user_language = get_current_language()
    if user_language != CFG.DEFAULT_LANGUAGE:
        stmt = stmt.options(joinedload(db.Attitude.translations))
    result = await a_session.scalars(stmt)
    return list(result.unique().all())


@alru_cache
async def read_unique_values(
    *,
    a_session: AsyncSession,
) -> list[db.UniqueValue]:
    result = await a_session.scalars(select(db.UniqueValue))
    return list(result.all())
