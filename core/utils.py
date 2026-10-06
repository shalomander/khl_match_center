import asyncio
import logging
from copy import deepcopy
from pathlib import Path

logger = logging.getLogger()
running_tasks = {}

def singleton_task(func):
    async def wrapped(*args, **kwargs):
        k_args=list(sorted(deepcopy(args)))
        k = f'{func.__name__};{k_args};{kwargs}'
        if k in running_tasks:
            logger.warning(f"Функция {k} уже запущена")
            return await running_tasks[k]
        task = asyncio.create_task(func(*args, **kwargs))
        running_tasks[k] = task
        try:
            return await task
        finally:
            running_tasks.pop(k, None)
    return wrapped

def get_modules(path):
    fs = [f for f in Path(path).rglob('*.py') if not f.name.startswith('_')]
    return [str(f).replace('/', '.')[:-3] for f in fs]

