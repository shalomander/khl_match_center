import asyncio
import importlib
import inspect
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.utils.pkg import get_modules

logger = logging.getLogger()

def autodiscover_tasks(scheduler:AsyncIOScheduler = None):
    if scheduler:
        for module_path in get_modules('apps'):
            if module_path.endswith('tasks'):
                module = importlib.import_module(module_path)
                for task in getattr(module, 'tasks', []):
                    try:
                        scheduler.add_job(**task)
                    except Exception as e:
                        logger.error(f'Ошибка добавления задачи: {repr(e)}')


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    autodiscover_tasks(scheduler)
    scheduler.start()
    return AsyncIOScheduler()
