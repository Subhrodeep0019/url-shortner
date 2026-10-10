from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.redis_client import get_redis
from src.db.models import Link
from src.db.db import get_session

from src.link.schemas import LinkCreateModel

from src.errors import (ReservedAliasError, AliasTakenError,
                        CodeGenerationError, LinkExpiredError)

import string
import json
from datetime import datetime, timezone

MAX_CODE_ATTEMPTS = 3
BASE62 = string.digits + string.ascii_lowercase + string.ascii_uppercase
BANNED_WORDS = {"login", "signup", "verify", "account", "password", "reset", "support",
                "contact", "billing", "secure", "admin", "root", "home", "help", "about",
                "urlshortner", "official"}


def is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return False
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return expires_at <= now


# service class
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




    async def cache_link(self,short_code: str, long_url: str, is_active: bool = True, expires_at: datetime | None = None) -> None:
        ex_ttl = None
        if expires_at is not None:
            if is_expired(expires_at):
                return

            now = datetime.now(timezone.utc).replace(tzinfo=None)
            ex_ttl = int((expires_at - now).total_seconds())
            if ex_ttl <= 0:
                return

        cache_data = json.dumps({
            "url": long_url,
            "is_active": is_active,
            "expires_at": expires_at.isoformat() if expires_at else None
        })

        # cache link
        await self.redis_session.set(short_code, cache_data, ex=ex_ttl)




    async def create_link(self, link_payload: LinkCreateModel) -> Link:
        word = link_payload.custom_alias
        # if alias is banned
        if word is not None and  word.lower() in BANNED_WORDS:
            raise ReservedAliasError()

        session = self.db_session
        link_data = link_payload.model_dump(exclude={"custom_alias"})
        link_data["long_url"] = str(link_payload.long_url)

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
            await self.cache_link(short, str(link_payload.long_url), expires_at=link_payload.expires_at)
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
        await self.cache_link(short_code, str(link.long_url), link.is_active, link.expires_at)

        # validating the link
        if not link.is_active:
            return None
        if is_expired(link.expires_at):
            raise LinkExpiredError()

        return link.long_url




    async def soft_delete(self, short_code) -> bool:
        statement = select(Link).where(Link.short_code==short_code)

        result = await self.db_session.exec(statement)
        link: Link = result.first()

        if link is None:
            return False

        link.is_active=False
        await self.db_session.commit()

        # update the cache record
        await self.cache_link(short_code, str(link.long_url), False, link.expires_at)

        return True



def get_link_service(session=Depends(get_session), redis=Depends(get_redis)) -> LinkService:
    return LinkService(session, redis)