import logging
from typing import Annotated, AsyncGenerator, TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.games.repositories import GameRepository
from apps.teams.repositories import TeamRepository
from apps.tournaments.repositories import TournamentRepository, SeasonRepository
from core.db.session import SessionLocal

logger = logging.getLogger()
R = TypeVar("R")

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.exception(f"Откат транзакции: {e}")
            raise
        finally:
            await session.close()

def repo_dep(repo_cls: type[R]):
    def _get_repo(session: SessionDep) -> R:
        return repo_cls(session)
    return Annotated[R, Depends(_get_repo)]

SessionDep = Annotated[AsyncSession, Depends(get_session)]
GameRepo = repo_dep(GameRepository)
TournamentRepo = repo_dep(TournamentRepository)
SeasonRepo = repo_dep(SeasonRepository)
TeamRepo = repo_dep(TeamRepository)