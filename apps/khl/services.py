from sqlalchemy import update, select

from apps.khl.models import Season, Tournament
from core.db.service import DbService


class TournamentService(DbService):
    model = Tournament

    async def set_current(self, t: Tournament):
        await self.db.execute(update(self.model).where(self.model.khl_id!=t.khl_id).values({'current': False}))
        await self.db.execute(update(self.model).where(self.model.khl_id==t.khl_id).values({'current': True}))
        await self.db.commit()
        await self.db.refresh(t)

    async def get_current(self):
        return await self.db.scalar(select(self.model).where(self.model.current==True))