import sys

from loguru import logger

logger.remove()

logger.add(
    '/app/logs/logger_log.log',
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
