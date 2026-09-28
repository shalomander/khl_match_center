import logging
from typing import List, Any

from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import func, select, text, inspect, update
from sqlalchemy.exc import IntegrityError

from core.db.base import Base
from core.dependencies import DBDependency

logger=logging.getLogger()

class DbService:
    model: type[Base]

    def __init__(self, db: DBDependency, model: type[Base]):
        self.db = db
        if model:
            self.model = model

    @property
    def pk_name(self):
        return inspect(self.model).primary_key[0].name

    async def count(self):
        return await self.db.scalar(select(func.count()).select_from(self.model))

    async def is_empty(self):
        return (await self.count())==0

    async def add_all(self, objects: List[dict]):
        self.db.add_all([self.model(**model_dict) for model_dict in objects])
        await self.db.commit()

    async def get_all(self, order_by: str=None):
        return await self.db.scalars(
            select(self.model).order_by(text(order_by or f'{self.pk_name} desc'))
        )

    async def paginate(self, order_by: str=None):
        return await apaginate(
            self.db,
            select(self.model).order_by(text(order_by or f'{self.pk_name} desc'))
        )

    async def first(self, order_by: str=None, **kwargs):
        return await self.db.scalar(
            select(self.model).filter_by(**kwargs).order_by(text(order_by or f'{self.pk_name} desc')).limit(1)
        )

    async def exists(self, *args, **kwargs):
        return await self.db.scalar(select(select(self.model).filter_by(**kwargs).exists()))

    async def _do_or_create(self, action:str, defaults:dict[str, Any]=None, **kwargs):
        created=False
        commit=False
        defaults = {} if defaults is None else defaults
        try:
            if obj:=await self.db.scalar(select(self.model).filter_by(**kwargs)):
                if action == 'update':
                    updates={k:v for k,v in defaults.items() if hasattr(obj, k) and getattr(obj, k, None) != v}
                    if updates:
                        await self.db.execute(update(self.model).filter_by(**{
                            self.pk_name:getattr(obj, self.pk_name, None)
                        }).values(**updates))
                        commit=True
            else:
                obj=self.model(**kwargs, **defaults)
                self.db.add(obj)
                created = True
            if commit:
                await self.db.commit()
                await self.db.refresh(obj)
            return obj, created
        except IntegrityError as e:
            logger.error(f'Ошибка добавления записи {self.model.__name__}: {e}. Откат транзакции')
            await self.db.rollback()


    async def get_or_create(self, defaults:dict[str, Any]=None, **kwargs):
        return await self._do_or_create('get', defaults, **kwargs)

    async def update_or_create(self, defaults:dict[str, Any]=None, **kwargs):
        return await self._do_or_create('update', defaults, **kwargs)