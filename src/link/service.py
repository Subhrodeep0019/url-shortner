from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.redis_client import get_redis
from src.db.models import Link
from src.db.db import get_session

from src.link.schemas import LinkCreateModel

from src.errors import ReservedAliasError, AliasTakenError, CodeGenerationError

import string
import json

MAX_CODE_ATTEMPTS = 3
BASE62 = string.digits + string.ascii_lowercase + string.ascii_uppercase
BANNED_WORDS = {"login", "signup", "verify", "account", "password", "reset", "support",
                "contact", "billing", "secure", "admin", "root", "home", "help", "about",
                "urlshortner", "official"}

class LinkService:
    # base 62 encoding algorithm
    @staticmethod
    def encode(base: int) -> str:
        code = ""
        if base==0:
            return "0"
        while base > 0:
            code = BASE62[base%62] + code
            base //= 62
        return code

    def __init__(self, session: AsyncSession, redis: Redis):
        self.db_session = session
        self.redis_session = redis

    async def create_code(self) -> str:
        counter = await self.redis_session.incr("link_counter")
        return self.encode(counter)

    async def cache_link(self,short_code: str, long_url: str, is_active: bool = True) -> None:
        cache_data = json.dumps({
            "url": long_url,
            "is_active": is_active
        })
        await self.redis_session.set(short_code, cache_data)

    async def create_link(self, link_payload: LinkCreateModel) -> Link:
        word = link_payload.custom_alias
        # if alias is banned
        if word is not None and  word.lower() in BANNED_WORDS:
            raise ReservedAliasError()

        session = self.db_session
        link_data = link_payload.model_dump(mode="json", exclude={"custom_alias"})

        for _ in range(MAX_CODE_ATTEMPTS):
            short = word if word is not None else await self.create_code()
            new_link = Link(**link_data, short_code=short)

            try:
                session.add(new_link)
                await session.commit()
                await session.refresh(new_link)
            except IntegrityError:
                await session.rollback()
                if word is not None:
                    raise AliasTakenError()
                continue

            # cache write
            await self.cache_link(short, str(link_payload.long_url))
            return new_link

        # can't generate unique short code even after 3 tries
        raise CodeGenerationError()

    async def get_long_url(self, short_code) -> str | None:

        # check cache first
        cache_data = await self.redis_session.get(short_code)
        if cache_data:
            data = json.loads(cache_data)
            return data["url"] if data["is_active"] else None

        # db hit
        statement = select(Link).where(Link.short_code==short_code)
        result = await self.db_session.exec(statement) # type: ignore[attr-defined]
        # noinspection PyUnresolvedReferences
        link: Link | None = result.first()

        if link is None:
            return None

        # lazy load -> cache write after cache miss and db hit
        await self.cache_link(short_code, str(link.long_url), link.is_active)

        return link.long_url if link.is_active else None

    async def soft_delete(self, short_code) -> bool:
        statement = select(Link).where(Link.short_code==short_code)

        result = await self.db_session.exec(statement)
        link: Link = result.first()

        if link is None:
            return False

        link.is_active=False
        await self.db_session.commit()

        # update the cache record
        await self.cache_link(short_code, str(link.long_url), False)

        return True



def get_link_service(session=Depends(get_session), redis=Depends(get_redis)) -> LinkService:
    return LinkService(session, redis)