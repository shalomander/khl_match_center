import logging
from datetime import datetime, timedelta
from typing import List

from apps.khl.models import Tournament, Game, Arena
from apps.khl.pydantic import CalendarGame
from core.db.service import DbService

logger = logging.getLogger(__name__)


class TournamentService(DbService):
    model = Tournament

    async def set_current(self, t: Tournament):
        await self.db.execute(self._update(where=[self.model.khl_id != t.khl_id], values={'current': False}))
        await self.db.execute(self._update(where=[self.model.khl_id == t.khl_id], values={'current': True}))
        await self.db.commit()
        await self.db.refresh(t)

    async def get_current(self):
        return await self.db.scalar(self._select(where=[self.model.current == True]))


class ArenaService(DbService):
    model = Arena

    async def update_from_calendar(self, arenas: List[dict]):
        await self.add_all([
            {'khl_id': a['id'], 'city': a['city']}
            for a in arenas if a['id'] not in [arena.pk for arena in await self.all()]
        ])


class GameService(DbService):
    model = Game

    async def update_from_calendar(self, games: List[dict]):
        dt = datetime.now()
        for game in games:
            g = CalendarGame(**game)
            too_old = g.is_over and g.start_at and g.start_at < dt - timedelta(days=2)
            too_far = g.start_at and g.start_at > dt + timedelta(days=2)
            if (too_old or too_far) and await self.exists(filter_by={'khl_id': g.khl_id}):
                continue
            obj, created = await self.update_or_create(khl_id=g.khl_id, defaults=g.model_dump())
            logger.warning(f'Данные игры {obj.pk} {"добавлены" if created else "обновлены"} из календаря')
