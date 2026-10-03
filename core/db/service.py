import logging
from typing import List

from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import func, select, text, update, inspect
from sqlalchemy.exc import IntegrityError

from core.db.base import Base
from core.dependencies import DBDependency

logger = logging.getLogger()


class DbService:
    model: type[Base]

    def __init__(self, db: DBDependency, model: type[Base] = None):
        self.db = db
        if model:
            self.model = model


    @property
    def model_pk_name(self)->str:
        return inspect(self.model).primary_key[0].name


    def _build_stmt(self, expr, **kwargs):
        stmt = expr(self.model)
        if 'filter' in kwargs and isinstance(kwargs['filter'], list):
            stmt = stmt.filter(*kwargs['filter'])
        if 'where' in kwargs and isinstance(kwargs['where'], list):
            stmt = stmt.where(*kwargs['where'])
        if 'filter_by' in kwargs and isinstance(kwargs['filter_by'], dict):
            stmt = stmt.filter_by(**kwargs['filter_by'])
        if 'values' in kwargs and isinstance(kwargs['values'], dict):
            stmt = stmt.values(**kwargs['values'])
        if 'limit' in kwargs and isinstance(kwargs['limit'], int):
            stmt = stmt.limit(kwargs['limit'])
        if hasattr(expr, 'order_by'):
            if not 'order_by' in kwargs:
                kwargs['order_by'] = [text(f'{self.model_pk_name} desc')]
            elif not isinstance(kwargs['order_by'], list):
                kwargs['order_by'] = [kwargs['order_by']]
            stmt = stmt.order_by(*kwargs['order_by'])
        return stmt

    def _select(self, **kwargs):
        return self._build_stmt(select, **kwargs)

    def _update(self, **kwargs):
        return self._build_stmt(update, **kwargs)

    async def count(self):
        return await self.db.scalar(select(func.count()).select_from(self.model))

    async def is_empty(self):
        return (await self.count()) == 0

    async def exists(self, **kwargs):
        return await self.db.scalar(select(self._build_stmt(select, **kwargs).exists()))

    async def all(self, **kwargs):
        return await self.db.scalars(self._select(**kwargs))

    async def first(self, **kwargs):
        return await self.db.scalar(self._select(**kwargs).limit(1))

    async def paginate(self, **kwargs):
        return await apaginate(self.db, self._select(**kwargs))

    async def _do_or_create(self, action: str, **kwargs):
        created = False
        skip_commit = False
        defaults = kwargs.pop('defaults', {})
        try:
            if obj := await self.first(filter_by=kwargs):
                if action == 'update':
                    updates = {k: v for k, v in defaults.items() if hasattr(obj, k) and getattr(obj, k, None) != v}
                    if updates:
                        await self.db.execute(self._build_stmt(
                            update, filter_by={self.model_pk_name: obj.pk}, values=updates
                        ))
                    else:
                        skip_commit=True
            else:
                obj = self.model(**kwargs, **defaults)
                self.db.add(obj)
                created = True
            if not skip_commit:
                await self.db.commit()
                await self.db.refresh(obj)
            return obj, created
        except IntegrityError as e:
            logger.error(f'Ошибка записи {self.model.__name__}: {e}. Откат транзакции')
            await self.db.rollback()

    async def get_or_create(self, **kwargs):
        return await self._do_or_create('get', **kwargs)

    async def update_or_create(self, **kwargs):
        return await self._do_or_create('update', **kwargs)

    async def add_all(self, objects: List[dict]):
        self.db.add_all([self.model(**model_dict) for model_dict in objects])
        await self.db.commit()


