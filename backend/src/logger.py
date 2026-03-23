import functools
import os
import sys
from typing import Callable

from loguru import logger

from src.config import CFG
from src.exceptions import get_error_msg

logger.remove()

logger.add(
    CFG.LOG_PATH,
    format=(
        '{time:YYYY-MM-DD HH:mm:ss} | {level} '
        '| {name}:{function}:{line} | {message}'
    ),
    enqueue=True,
    level='DEBUG',
    rotation='10 MB',
    retention='1 month',
)

logger.add(
    sys.stderr,
    format='{time} | {level} | {message}',
    level='DEBUG',
    enqueue=True,
)


def sync_catch(*, to_raise: bool):
    """Decorator to add logging to sync methods."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f'Worker {os.getpid()}. '
                    f'Error in {func_name=}: {get_error_msg(e)}'
                )
                if to_raise:
                    raise e

        return wrapper

    return decorator


def async_catch(*, to_raise: bool):
    """Decorator to add logging to async methods."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f'Worker {os.getpid()}. '
                    f'Error in {func_name=}: {get_error_msg(e)}'
                )
                raise e

        return wrapper

    return decorator
