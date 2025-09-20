import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .crud import sql


async def refresh_recommendations_task(session_factory):
    """
    Task to refresh the recommendations materialized view.
    """
    # start_time = asyncio.get_event_loop().time()

    try:
        async with session_factory() as session:
            await session.execute(sql.refresh_recommendations)
            print(
                f'{asyncio.get_event_loop().time()}: recommendations refreshed'
            )
            await session.commit()
            # duration = asyncio.get_event_loop().time() - start_time

    except Exception as e:
        raise e


def start_scheduler(session_factory) -> AsyncIOScheduler:
    """
    Initialize and configure the scheduler
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        refresh_recommendations_task,
        args=[session_factory],
        trigger=IntervalTrigger(
            # hours=cnst.RECOMMENDATIONS_UPDATE_INTERVAL_HOURS
            seconds=10
        ),
        id='refresh_recommendations',
        name='Refresh recommendations materialized view',
        replace_existing=True,
    )
    scheduler.start()
    # logger.info('Scheduler started.')
    print('Scheduler started.')
    return scheduler
