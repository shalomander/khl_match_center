import logging
from contextlib import suppress
from datetime import datetime, timedelta
from typing import List

from apps.games.models import Game
from apps.khl_data.pydantic import CalendarGame
from core.db.repository import BaseRepository

logger = logging.getLogger(__name__)


class GameRepository(BaseRepository[Game]):
    model = Game

    async def update_from_calendar(self, games: List[dict]):
        dt = datetime.now()
        for game in games:
            with suppress(Exception):
                g = CalendarGame(**game)
                too_old = g.is_over and g.start_at and g.start_at < dt - timedelta(days=2)
                too_far = g.start_at and g.start_at > dt + timedelta(days=2)
                if (too_old or too_far) and await self.exists(filter_by={'khl_id': g.khl_id}):
                    continue
                obj, created = await self.update_or_create(khl_id=g.khl_id, defaults=g.model_dump())
                logger.warning(f'Данные игры {obj.pk} {"добавлены" if created else "обновлены"} из календаря')
