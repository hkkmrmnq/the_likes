import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from . import constants as cnst
from .crud import sql


async def refresh_sim_scores_n_recommendations(session_factory):
    """
    Task to refresh the similarity_scores and recommendations
    materialized views.
    """

    try:
        start_time = asyncio.get_event_loop().time()
        async with session_factory() as session:
            await session.execute(sql.refresh_mat_view_similarity_scores)
            await session.commit()
            duration = asyncio.get_event_loop().time() - start_time
            print(f'similarity_scores refreshed in {duration}')

    except Exception as e:
        raise e

    try:
        start_time = asyncio.get_event_loop().time()
        async with session_factory() as session:
            await session.execute(sql.refresh_mat_view_recommendations)
            await session.commit()
            duration = asyncio.get_event_loop().time() - start_time
            print(f'recommendations refreshed in {duration}')

    except Exception as e:
        raise e


def start_scheduler(session_factory) -> AsyncIOScheduler:
    """
    Initialize and configure the scheduler
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        refresh_sim_scores_n_recommendations,
        args=[session_factory],
        trigger=IntervalTrigger(
            hours=cnst.RECOMMENDATIONS_UPDATE_INTERVAL_HOURS
        ),
        id='refresh_similarity_scores',
        name='Refresh similarity_scores materialized view',
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
