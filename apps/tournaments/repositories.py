import logging

from apps.tournaments.models import Tournament, Season
from core.db.repository import BaseRepository

logger = logging.getLogger(__name__)


class SeasonRepository(BaseRepository[Season]):
    model = Season

class TournamentRepository(BaseRepository[Tournament]):
    model = Tournament

    async def set_current(self, t: Tournament):
        await self.session.execute(self._update(where=[self.model.khl_id != t.khl_id], values={'current': False}))
        await self.session.execute(self._update(where=[self.model.khl_id == t.khl_id], values={'current': True}))
        await self.session.commit()
        await self.session.refresh(t)

    async def get_current(self):
        return await self.session.scalar(self._select(where=[self.model.current == True]))

    async def get_one_or_current(self, t_id):
        return  await self.first(khl_id=t_id) if isinstance(t_id, int) else await self.get_current()