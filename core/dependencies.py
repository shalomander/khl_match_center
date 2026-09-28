import logging
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.session import SessionLocal

logger = logging.getLogger()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.exception(f"Откат транзакции: {e}")
            raise
        finally:
            await session.close()

DBDependency = Annotated[AsyncSession, Depends(get_db)]