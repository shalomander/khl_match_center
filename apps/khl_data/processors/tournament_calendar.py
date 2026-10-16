import logging

from sqlalchemy.ext.asyncio.session import AsyncSession

from apps.games.repositories import GameRepository
from apps.khl_data.processors.base import BaseDataProcessor
from apps.khl_data.readers.tournament_calendar import TournamentCalendarReader
from apps.teams.repositories import ArenaRepository
from apps.tournaments.models import Tournament

logger=logging.getLogger()

class TournamentCalendarDataProcessor(BaseDataProcessor):
    def __init__(self, session: AsyncSession, reader: TournamentCalendarReader, tournament: Tournament):
        super().__init__(session, reader)
        self.tournament = tournament
        self.arn_repo=ArenaRepository(session)
        self.gm_repo=GameRepository(session)

    async def update_db(self, drop_old=False):
        if drop_old:
            await self._cleanup()
        if not self.reader.errors:
            await self.arn_repo.update_from_calendar(self.reader.arenas)
            await self.gm_repo.update_from_calendar(self.reader.games)
            logger.warning(f'Календарь турнира {self.tournament.khl_id} обновлен')
        else:
            logger.error(f'Ошибка получения календаря турнира {self.tournament.khl_id}: {self.reader.errors}')

