import redis

from src.config import CFG

redis_client = redis.Redis(
    host=CFG.REDIS_HOST,
    port=CFG.REDIS_PORT,
    db=CFG.REDIS_MAIN_DB,
    decode_responses=True,
    encoding='utf-8',
)
