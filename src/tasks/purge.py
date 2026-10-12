import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import col

from src.celery_app import c_app
from src.config import settings
from src.db.models import Link

logger = logging.getLogger(__name__)

BATCH_SIZE = 1


async def _purge_expired() -> int:
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    total = 0
    try:
        async with AsyncSession(engine) as session:
            while True:
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                result = await session.execute(
                    select(Link.uid)
                    .where(col(Link.expires_at).is_not(None), col(Link.expires_at) < now)
                    .limit(BATCH_SIZE)
                )
                ids = result.scalars().all()
                if not ids:
                    break
                await session.execute(delete(Link).where(col(Link.uid).in_(ids)))
                await session.commit()
                total += len(ids)
    finally:
        await engine.dispose()
    return total


@c_app.task(name="purge_expired_links")
def purge_expired_links() -> int:
    deleted = asyncio.run(_purge_expired())
    logger.info("Purged %d expired links", deleted)
    return deleted