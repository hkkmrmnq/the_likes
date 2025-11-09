import redis

from src.config.config import CFG

redis_client = redis.Redis(
    host=CFG.REDIS_HOST,
    port=CFG.REDIS_PORT,
    db=CFG.REDIS_DB,
    decode_responses=True,
)
