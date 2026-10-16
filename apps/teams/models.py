from typing import List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.base import Base

if TYPE_CHECKING:
    from apps.tournaments.models import SeasonTeam
    from apps.games.models import Game


class Team(Base):
    __tablename__ = "teams"

    khl_id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    image: Mapped[str] = mapped_column(nullable=True)
    seasons: Mapped[List["SeasonTeam"]] = relationship(
        "SeasonTeam",
        back_populates="team",
        lazy='selectin'
    )
    home_games: Mapped["Game"] = relationship(
        "Game",
        back_populates="home_team",
        foreign_keys="Game.home_team_id"
    )
    away_games: Mapped["Game"] = relationship(
        "Game",
        back_populates="visitor_team",
        foreign_keys="Game.visitor_team_id"
    )

    def __str__(self):
        city_str = f'({self.city})' if self.city else ''
        return f"{self.name}{city_str}" if self.name else "Новая команда"


class Arena(Base):
    __tablename__ = "arenas"

    khl_id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(255), nullable=True)

    games: Mapped["Game"] = relationship("Game", back_populates="arena", foreign_keys="Game.arena_id")

    def __str__(self):
        city_str = f'({self.city})' if self.city else ''
        return f"{self.name}{city_str}" if self.name else "Новая арена"
