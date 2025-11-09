import sys

from loguru import logger

from src.config.config import CFG

logger.remove()

logger.add(
    CFG.LOG_PATH,
    format=(
        '{time:YYYY-MM-DD HH:mm:ss} | {level} '
        '| {name}:{function}:{line} | {message}'
    ),
    level='DEBUG',
    rotation='10 MB',
    retention='1 month',
)

logger.add(
    sys.stderr,
    format='{time} | {level} | {message}',
    level='DEBUG',
)
