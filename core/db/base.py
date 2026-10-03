from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    @property
    def pk(self):
        return getattr(self, inspect(self.__class__).primary_key[0].name, None)
