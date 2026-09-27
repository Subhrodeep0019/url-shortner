import redis.asyncio as redis
from src.config import settings

client = redis.from_url(settings.REDIS_URL)

async def get_redis():
    async with client as c:
        yield c



