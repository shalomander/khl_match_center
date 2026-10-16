import logging
from typing import List

from apps.teams.models import Arena, Team
from core.db.repository import BaseRepository

logger = logging.getLogger(__name__)


class TeamRepository(BaseRepository[Team]):
    model = Team

class ArenaRepository(BaseRepository[Arena]):
    model = Arena

    async def update_from_calendar(self, arenas: List[dict]):
        await self.add_all([
            {'khl_id': a['id'], 'city': a['city']}
            for a in arenas if a['id'] not in [arena.pk for arena in await self.all()]
        ])