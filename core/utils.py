import asyncio
import functools
import logging
from copy import deepcopy
from pathlib import Path

from fastapi import HTTPException
from starlette.status import HTTP_404_NOT_FOUND

logger = logging.getLogger()
running_tasks = {}

def singleton_task(func):
    # Костыль для исключения наложения задач при запуске в обход планировщика
    async def wrapped(*args, **kwargs):
        args_slist = [str(a) for a in sorted(deepcopy(args))]
        kwargs_slist = [f'--{k}={str(kwargs[k])}' for k in sorted(kwargs.keys())]
        k = f'{func.__name__} {" ".join(args_slist+kwargs_slist)} {" ".join(kwargs_slist)}'
        if k in running_tasks:
            logger.warning(f"Функция уже запущена: {k}")
            return await running_tasks[k]
        task = asyncio.create_task(func(*args, **kwargs))
        running_tasks[k] = task
        try:
            return await task
        finally:
            running_tasks.pop(k, None)
    return wrapped

def task_info(msg):
    def decorator(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            logger.warning(f'Новая фоновая задача: {msg}')
            return await func(*args, **kwargs)
        return wrapped
    return decorator


def get_modules(path):
    fs = [f for f in Path(path).rglob('*.py') if not f.name.startswith('_')]
    return [str(f).replace('/', '.')[:-3] for f in fs]

def get_obj_diff(obj, new_values: dict):
    diff = {k: v for k, v in new_values.items() if hasattr(obj, k) and getattr(obj, k, None) != v}
    return diff

def get_or_raise_404(value):
    if not value:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND)
    return value