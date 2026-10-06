import importlib
import logging

from fastapi import APIRouter

from core.utils import get_modules

logger=logging.getLogger()

api_root='api'
api_router = APIRouter()

def autodiscover_routes():
    for module_path in get_modules(api_root):
        if module_path.endswith('endpoints'):
            try:
                module = importlib.import_module(module_path)
                route_prefix=f'/{"/".join(module_path.split(".")[:-1])}'
                api_router.include_router(getattr(module, 'router'), prefix=route_prefix)
            except Exception as e:
                logger.error(e)
    return api_router