from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    def extract_fields(self) -> dict:
        fields = {}
        for field in [x for x in dir(self) if not x.startswith('_') and x != 'metadata']:
            data = self.__getattribute__(field)
            try:
                fields[field] = data
            except TypeError:
                fields[field] = None
        return fields
