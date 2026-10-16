from sqlalchemy.orm import Mapped, mapped_column
from core.db.base import Base


class Coach(Base):
    __tablename__ = "coach"

    khl_id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=False)

class Referee(Base):
    __tablename__ = "referee"

    khl_id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=False)

class Player(Base):
    __tablename__ = "player"

    khl_id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=False)