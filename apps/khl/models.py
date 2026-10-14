import datetime
from typing import List

from sqlalchemy import String, ForeignKey, sql, UniqueConstraint
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
        # index=True
    )
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete='SET NULL'),
        nullable=False,
        # index=True
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


class Team(Base):
    __tablename__ = "teams"

    khl_id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=False)
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

    khl_id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(255), nullable=True)

    games: Mapped["Game"] = relationship("Game", back_populates="arena", foreign_keys="Game.arena_id")

    def __str__(self):
        city_str = f'({self.city})' if self.city else ''
        return f"{self.name}{city_str}" if self.name else "Новая арена"


class Game(Base):
    __tablename__ = "games"

    khl_id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=False)
    start_at: Mapped[datetime.datetime] = mapped_column(index=True, nullable=True)
    home_score: Mapped[int] = mapped_column(nullable=True)
    visitor_score: Mapped[int] = mapped_column(nullable=True)
    attendance: Mapped[int] = mapped_column(nullable=True)
    ots: Mapped[str] = mapped_column(String(2), nullable=True)
    is_over: Mapped[bool] = mapped_column(nullable=False, server_default=sql.false())
    broadcast_processed: Mapped[bool] = mapped_column(nullable=False, server_default=sql.false())
    protocol_processed: Mapped[bool] = mapped_column(nullable=False, server_default=sql.false())

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
        ForeignKey("arenas.khl_id", ondelete='SET NULL'),
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
        lazy="joined"
    )
    visitor_team: Mapped["Team"] = relationship(
        "Team",
        back_populates="away_games",
        foreign_keys=visitor_team_id,
        lazy="joined"
    )
    home_lineup: Mapped[List["GameLineup"]] = relationship(
        "GameLineup",
        primaryjoin="and_(Game.khl_id == GameLineup.game_id, GameLineup.team_side == 'A')",
        order_by="GameLineup.line_number",
        overlaps="visitor_lineup"
    )
    visitor_lineup: Mapped["GameLineup"] = relationship(
        "GameLineup",
        primaryjoin="and_(Game.khl_id == GameLineup.game_id, GameLineup.team_side == 'B')",
        order_by="GameLineup.line_number",
        overlaps="home_lineup"
    )
    arena: Mapped["Arena"] = relationship(
        "Arena",
        back_populates="games",
        foreign_keys=arena_id,
        lazy="joined"
    )

    def __str__(self):
        return f"Игра {self.khl_id}" if self.khl_id is not None else "Новая игра"


class GameLineup(Base):
    __tablename__ = "game_lineups"

    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.khl_id", ondelete='CASCADE'),
        nullable=False,
        primary_key=True
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.khl_id", ondelete='SET NULL'),
        nullable=False,
        primary_key=True
    )
    team_side: Mapped[str] = mapped_column(String(1), primary_key=True, nullable=False)
    line_number: Mapped[int] = mapped_column(nullable=False)

    team = relationship(
        "Team",
    )