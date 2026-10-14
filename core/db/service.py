import logging
from contextlib import suppress
from typing import List

from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import func, select, text, update, inspect, TextClause
from sqlalchemy.exc import IntegrityError, DatabaseError

from core.db.base import Base
from core.dependencies import DBDependency
from core.utils import get_obj_diff

logger = logging.getLogger()


class DbService:
    model: type[Base]

    def __init__(self, db: DBDependency, model: type[Base] = None):
        self.db = db
        if model:
            self.model = model

    @property
    def model_pk_name(self) -> str:
        return inspect(self.model).primary_key[0].name

    def _build_stmt(self, expr, **kwargs):
        queries = {}
        stmt = expr(self.model)
        for q in ['filter', 'where', 'values', 'limit', 'order_by', 'options']:
            queries[q] = kwargs.pop(q, None)
        if 'filter_by' in kwargs and isinstance(kwargs['filter_by'], dict):
            kwargs.update(kwargs.pop('filter_by', {}))
        queries['filter_by'] = kwargs
        if isinstance(queries['filter'], list):
            stmt = stmt.filter(*queries['filter'])
        if isinstance(queries['where'], list):
            stmt = stmt.where(*queries['where'])
        if queries['filter_by'] and isinstance(queries['filter_by'], dict):
            stmt = stmt.filter_by(**queries['filter_by'])
        if queries['values'] and isinstance(queries['values'], dict):
            stmt = stmt.values(**queries['values'])
        if isinstance(queries['limit'], int):
            stmt = stmt.limit(queries['limit'])
        if isinstance(queries['options'], list):
            stmt = stmt.options(queries['options'])
        if hasattr(stmt, 'order_by'):
            stmt = stmt.order_by(*self._prepare_order_expr_list(queries.get('order_by', [])))
        return stmt

    def _prepare_order_expr_list(self, order_by):
        expr_list = []
        if not order_by:
            expr_list.append(text(f'{self.model_pk_name} desc'))
        elif isinstance(order_by, str):
            expr_list.append(text(order_by))
        elif isinstance(order_by, list):
            for expr in order_by:
                with suppress(Exception):
                    expr_list.append(text(expr) if not isinstance(expr, TextClause) else expr)
        return expr_list

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
        created, refresh = False, False
        defaults = kwargs.pop('defaults', {})
        try:
            async with self.db.begin_nested():
                if obj := await self.first(filter_by=kwargs):
                    if action == 'update':
                        if (updates:=get_obj_diff(obj, defaults)) or True:
                            logger.warning(f'обновление: {updates}')
                            await self.db.execute(self._update(filter_by={self.model_pk_name: obj.pk}, values=updates))
                            refresh=True
                else:
                    obj = self.model(**kwargs | defaults)
                    self.db.add(obj)
                    created = True
                await self.db.flush()
                if refresh:
                    await self.db.refresh(obj)
        except (DatabaseError, IntegrityError) as e:
                logger.error(f'Ошибка записи {self.model.__name__}: {e}')
        return obj, created

    async def get_or_create(self, **kwargs):
        return await self._do_or_create('get', **kwargs)

    async def update_or_create(self, **kwargs):
        return await self._do_or_create('update', **kwargs)

    async def update(self, **kwargs):
        if kwargs.get('values'):
            async with self.db.begin_nested():
                await self.db.flush(await self.db.execute(self._update(**kwargs)))

    async def add_all(self, objects: List[dict]):
        self.db.add_all([self.model(**model_dict) for model_dict in objects])
        await self.db.flush()
