import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import constants as CNST
from .crud import sql


async def refresh_materialized_views(session_factory):
    f"""
    Task to refresh {', '.join(CNST.MATERIALIZED_VIEW_NAMES)}
    materialized views.
    """

    for name in CNST.MATERIALIZED_VIEW_NAMES:
        try:
            start_time = asyncio.get_event_loop().time()
            async with session_factory() as session:
                await session.execute(getattr(sql, f'refresh_mat_view_{name}'))
                await session.commit()
            duration = asyncio.get_event_loop().time() - start_time
            print(f'{name} refreshed in {duration}')

        except Exception as e:
            raise e


def start_scheduler(session_factory) -> AsyncIOScheduler:
    """
    Initialize and configure the scheduler
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        refresh_materialized_views,
        args=[session_factory],
        trigger=IntervalTrigger(
            hours=CNST.RECOMMENDATIONS_UPDATE_INTERVAL_HOURS
        ),
        id='refresh_similarity_scores',
        name='Refresh similarity_scores materialized view',
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
