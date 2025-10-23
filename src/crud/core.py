from async_lru import alru_cache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, contains_eager, joinedload

from .. import db as db
from ..config import constants as CNST
from ..context import get_current_language
from ..exceptions import exceptions as exc


async def read_definitions(*, a_session: AsyncSession) -> list[db.ValueTitle]:
    user_language = get_current_language()
    if user_language == CNST.LANGUAGE_DEFAULT:
        stmt = select(db.ValueTitle).options(joinedload(db.ValueTitle.aspects))
    else:
        vt_trans = aliased(db.ValueTitleTranslation)
        asp_trans = aliased(db.AspectTranslation)

        stmt = (
            select(db.ValueTitle)
            .join(vt_trans, db.ValueTitle.translations)
            .join(db.ValueTitle.aspects)
            .join(asp_trans, db.Aspect.translations)
            .options(
                contains_eager(db.ValueTitle.translations, alias=vt_trans),
                contains_eager(db.ValueTitle.aspects).contains_eager(
                    db.Aspect.translations, alias=asp_trans
                ),
            )
            .where(
                vt_trans.language_code == user_language,
                asp_trans.language_code == user_language,
            )
        )
    results = await a_session.scalars(stmt)
    definitions = list(results.unique().all())
    if not definitions:
        raise exc.ServerError('Definitions not found.')
    return definitions


async def read_attitudes(*, a_session: AsyncSession) -> list[db.Attitude]:
    stmt = select(db.Attitude)
    user_language = get_current_language()
    if user_language != CNST.LANGUAGE_DEFAULT:
        stmt = stmt.options(joinedload(db.Attitude.translations))
    result = await a_session.scalars(stmt)
    attitudes = list(result.unique().all())
    if not attitudes:
        raise exc.ServerError('Attitudes not found.')
    return attitudes


@alru_cache
async def read_unique_values(
    *,
    a_session: AsyncSession,
) -> list[db.UniqueValue]:
    result = await a_session.scalars(select(db.UniqueValue))
    return list(result.all())
