from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud
from ..config import constants as CNST
from ..db import session_factory
from . import sql


async def materialized_view_exists(name: str, session: AsyncSession) -> bool:
    """
    Check if materialized with the given name view exists.
    Returns True or False.
    name: name of a materialized view.
    """
    result = await session.execute(sql.mat_view_exists, {'name': name})
    return bool(result.scalar())


async def execute_sequence(raw_queries: list[str]) -> None:
    for query in raw_queries:
        async with session_factory() as session:
            await session.execute(text(query))
            await session.commit()


async def check_basic_data():
    async with session_factory() as session:
        await crud.read_definitions(CNST.LANGUAGE_DEFAULT, session)
        await crud.read_attitudes(CNST.LANGUAGE_DEFAULT, session)


async def manage_precalculations():
    for name in CNST.MATERIALIZED_VIEW_NAMES:
        async with session_factory() as session:
            if await crud.materialized_view_exists(name, session):
                await session.execute(getattr(sql, f'refresh_mat_view_{name}'))
            else:
                await execute_sequence(getattr(sql, f'prepare_{name}'))
            await session.commit()
