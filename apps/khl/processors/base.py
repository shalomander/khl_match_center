import logging
from abc import abstractmethod, ABC
from typing import Type

from sqlalchemy.ext.asyncio.session import AsyncSession

from apps.khl.readers.base import KhlReader

logger = logging.getLogger()

def with_error_logging(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            err_msg = f'Ошибка обновления данных игры[{func.__name__}]: {repr(e)}'
            self.error_list.append(err_msg)
            logger.exception(err_msg)
    return wrapper

class BaseDataProcessor(ABC):

    def __init__(self, session: AsyncSession, reader):
        self.session = session
        self.reader = reader
        self.error_list = []

    @abstractmethod
    async def update_db(self, drop_old=False):
        ...

    async def _cleanup(self):
        ...