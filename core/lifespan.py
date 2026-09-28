import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from sqlalchemy import text

from core.apscheduler import setup_scheduler
from core.db.session import engine

logger = logging.getLogger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    scheduler:AsyncIOScheduler = setup_scheduler()
    yield
    if scheduler and scheduler.running:
        scheduler.shutdown()
