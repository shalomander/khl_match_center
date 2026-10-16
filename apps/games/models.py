from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import String, sql, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.base import Base

if TYPE_CHECKING:
    from apps.tournaments.models import Tournament
    from apps.teams.models import Team, Arena


class Game(Base):
    __tablename__ = "games"

    khl_id: Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=False)
    start_at: Mapped[datetime] = mapped_column(index=True, nullable=True)
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

    team = relationship("Team")