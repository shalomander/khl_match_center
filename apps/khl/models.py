import datetime
from typing import List

from sqlalchemy import String, ForeignKey, sql
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

from core.db.base import Base


class Conference(Base):
    __tablename__ = "conferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)

    teams: Mapped["Team"] = relationship(
        "Team",
        back_populates="conference"
    )


class Division(Base):
    __tablename__ = "divisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[int] = mapped_column(String(30), nullable=False, unique=True)

    teams: Mapped["Team"] = relationship(
        "Team",
        back_populates="division"
    )


class SeasonTeam(Base):
    __tablename__ = "season_teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.khl_id", ondelete='SET NULL'),
        nullable=False,
        index=True
    )
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete='SET NULL'),
        nullable=False,
        index=True
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


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    year_start: Mapped[int] = mapped_column(index=True, nullable=False)
    year_end: Mapped[int] = mapped_column(index=True, nullable=False)

    tournaments: Mapped["Tournament"] = relationship(
        "Tournament",
        back_populates="season"
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

    khl_id: Mapped[int] = mapped_column(primary_key=True)
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
        lazy="selectin"
    )
    games: Mapped["Game"] = relationship(
        "Game",
        back_populates="tournament",
        lazy="selectin"
    )

    def __str__(self):
        if self.khl_id:
            return f"{self.PART_VERBOSE.get(self.part, 'Турнир КХЛ')}, {self.season}"
        else:
            return "Новый турнир"


class Team(Base):
    __tablename__ = "teams"

    khl_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    image: Mapped[str] = mapped_column(nullable=True)
    conference_id: Mapped[int] = mapped_column(
        ForeignKey("conferences.id", ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    division_id: Mapped[int] = mapped_column(
        ForeignKey("divisions.id", ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    conference: Mapped["Conference"] = relationship(
        "Conference",
        back_populates="teams"
    )
    division: Mapped["Division"] = relationship(
        "Division",
        back_populates="teams"
    )
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

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=True)

    games: Mapped["Game"] = relationship("Game", back_populates="arena", foreign_keys="Game.arena_id")

    def __str__(self):
        city_str = f'({self.city})' if self.city else ''
        return f"{self.name}{city_str}" if self.name else "Новая арена"


class Game(Base):
    __tablename__ = "games"

    khl_id: Mapped[int] = mapped_column(primary_key=True)
    start_at: Mapped[datetime.datetime] = mapped_column(index=True, nullable=True)
    finish_at: Mapped[datetime.datetime] = mapped_column(index=True, nullable=True)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.khl_id", ondelete='SET NULL'),
        nullable=False,
        index=True
    )
    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.khl_id", ondelete='SET NULL'),
        nullable=False,
        index=True
    )
    visitor_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.khl_id", ondelete='SET NULL'),
        nullable=False,
        index=True
    )
    arena_id: Mapped[int] = mapped_column(
        ForeignKey("arenas.id", ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    tournament: Mapped["Tournament"] = relationship(
        "Tournament",
        back_populates="games"
    )
    home_team: Mapped["Team"] = relationship(
        "Team",
        back_populates="home_games",
        foreign_keys=home_team_id,
        lazy="selectin"
    )
    visitor_team: Mapped["Team"] = relationship(
        "Team",
        back_populates="away_games",
        foreign_keys=visitor_team_id,
        lazy="selectin"
    )
    arena: Mapped["Arena"] = relationship(
        "Arena",
        back_populates="games",
        foreign_keys=arena_id
    )

    def __str__(self):
        return f"Игра {self.khl_id}" if self.khl_id is not None else "Новая игра"
