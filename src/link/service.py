from fastapi import Depends
from redis.asyncio import Redis

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.redis_client import get_redis
from src.db.models import Link
from src.db.db import get_session

from src.link.schemas import LinkCreateModel

import string


class LinkService:
    # base 62 encoding algorithm
    BASE62 = string.digits + string.ascii_lowercase + string.ascii_uppercase
    @staticmethod
    def encode(base: int) -> str:
        code = ""
        if base==0:
            return "0"
        while base > 0:
            code = LinkService.BASE62[base%62] + code
            base //= 62
        return code

    def __init__(self, session: AsyncSession, redis: Redis):
        self.db_session = session
        self.redis_session = redis

    async def create_code(self) -> str:
        counter = await self.redis_session.incr("link_counter")
        return self.encode(counter)

    async def create_link(self, link_payload: LinkCreateModel) -> Link:
        short = await self.create_code()
        new_link = Link(
            **link_payload.model_dump(mode="json"),
            short_code=short,
        )

        session = self.db_session

        session.add(new_link)
        await session.commit()
        await session.refresh(new_link)

        return new_link

    async def get_long_url(self, short_code) -> str | None:
        statement = select(Link).where(Link.short_code==short_code, Link.is_active==True)
        result = await self.db_session.exec(statement)
        link: Link | None = result.first()

        if link is None:
            return None

        return link.long_url

    async def soft_delete(self, short_code) -> bool:
        statement = select(Link).where(Link.short_code==short_code)

        result = await self.db_session.exec(statement)
        link: Link = result.first()

        if link is None:
            return False

        link.is_active=False
        await self.db_session.commit()
        return True



def get_link_service(session=Depends(get_session), redis=Depends(get_redis)) -> LinkService:
    return LinkService(session, redis)