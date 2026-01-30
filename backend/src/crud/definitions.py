from async_lru import alru_cache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, contains_eager, joinedload

from src import db
from src.config import CFG


async def read_values(
    *, user_language: str = CFG.DEFAULT_LANGUAGE, asession: AsyncSession
) -> list[db.Value]:
    if user_language == CFG.DEFAULT_LANGUAGE:
        stmt = select(db.Value).options(joinedload(db.Value.aspects))
    else:
        vt_translation = aliased(db.ValueTranslation)
        asp_translation = aliased(db.AspectTranslation)

        stmt = (
            select(db.Value)
            .join(vt_translation, db.Value.translations)
            .join(db.Value.aspects)
            .join(asp_translation, db.Aspect.translations)
            .options(
                contains_eager(db.Value.translations, alias=vt_translation),
                contains_eager(db.Value.aspects).contains_eager(
                    db.Aspect.translations, alias=asp_translation
                ),
            )
            .where(
                vt_translation.language_code == user_language,
                asp_translation.language_code == user_language,
            )
        )
    results = await asession.scalars(stmt)
    return list(results.unique().all())


async def read_attitudes(
    *, user_language: str = CFG.DEFAULT_LANGUAGE, asession: AsyncSession
) -> list[db.Attitude]:
    stmt = select(db.Attitude)
    if user_language != CFG.DEFAULT_LANGUAGE:
        stmt = stmt.options(joinedload(db.Attitude.translations))
    result = await asession.scalars(stmt)
    return list(result.unique().all())


@alru_cache
async def read_unique_values(
    *,
    asession: AsyncSession,
) -> list[db.UniqueValue]:
    result = await asession.scalars(select(db.UniqueValue))
    return list(result.all())
