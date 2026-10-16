from typing import List, TYPE_CHECKING

from sqlalchemy import String, ForeignKey, UniqueConstraint, sql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.base import Base

if TYPE_CHECKING:
    from apps.games.models import Game


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    year_start: Mapped[int] = mapped_column(index=True, nullable=False)
    year_end: Mapped[int] = mapped_column(index=True, nullable=False)

    tournaments: Mapped[List["Tournament"]] = relationship(
        "Tournament",
        back_populates="season",
        lazy='selectin'
    )
    teams: Mapped[List["SeasonTeam"]] = relationship(
        "SeasonTeam",
        back_populates="season",
        lazy='selectin'
    )

    def __str__(self):
        return f"Сезон {self.year_start}-{self.year_end}" if self.id else "Новый сезон"


class Tournament(Base):
    PART_VERBOSE = {
        'regular': 'Регулярный чемпионат',
        'playoff': 'Плей-офф'
    }
    __tablename__ = "tournaments"

    khl_id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=False)
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete='SET NULL'),
        nullable=False,
        index=True
    )
    part: Mapped[str] = mapped_column(index=True, nullable=False)
    current: Mapped[bool] = mapped_column(index=True, nullable=False, server_default=sql.false())

    season: Mapped["Season"] = relationship(
        "Season",
        back_populates="tournaments",
        lazy="joined"
    )
    games: Mapped[List["Game"]] = relationship(
        "Game",
        back_populates="tournament",
        lazy="selectin"
    )

    def __str__(self):
        if self.khl_id:
            return f"{self.PART_VERBOSE.get(self.part, 'Турнир КХЛ')}, {self.season}"
        else:
            return "Новый турнир"


class SeasonTeam(Base):
    __tablename__ = "season_teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.khl_id", ondelete='SET NULL'),
        nullable=False,
    )
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete='SET NULL'),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    image: Mapped[str] = mapped_column(nullable=True)

    season = relationship(
        "Season",
        back_populates='teams',
        lazy="selectin"
    )
    team = relationship(
        "Team",
        back_populates='seasons',
        lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint('season_id', 'team_id'),
    )
