import logging

from sqlalchemy.ext.asyncio.session import AsyncSession

from apps.games.models import Game
from apps.games.repositories import GameRepository
from apps.khl_data.processors.base import BaseDataProcessor, with_error_logging
from apps.khl_data.pydantic import BroadcastGameInfo
from apps.khl_data.readers.game_broadcast import GameBroadcastReader
from core.utils import get_obj_diff

logger=logging.getLogger()

class GameBroadcastDataProcessor(BaseDataProcessor):
    def __init__(self, session: AsyncSession, reader: GameBroadcastReader, game: Game):
        super().__init__(session, reader)
        self.game = game
        self.game_updates = {} # Изменения объекта игры из разных блоков данных
        self.gm_repo=GameRepository(session)

    async def update_db(self, drop_old=False):
        if drop_old:
            await self._cleanup()
        if not self.reader.errors:
            # self._update_teams()
            # self._update_referees()
            # self._update_coaches()
            # self._update_lineup()
            # self._update_player_stats()
            # self._update_team_stats()
            # self._update_goals()
            # self._update_disallowed_goals()
            # self._update_penalties()
            # self._update_video_reviews()
            # self._update_penalty_shots()
            # self._update_shootouts()
            # self._update_goalie_subs()
            await self._update_game()
            logger.warning(f'Трансляция игры {self.game.khl_id} обработана')
        else:
            logger.warning(f'Ошибка обработки трансляции игры {self.game.khl_id}: {self.reader.errors}')

    async def _cleanup(self):
        ...

    def _update_teams(self):
        ...

    async def _update_game(self):
        self.game_updates.update(BroadcastGameInfo(**self.reader.info).model_dump())
        await self.gm_repo.update(
            filter_by={'khl_id': self.game.pk},
            values=get_obj_diff(self.game, self.game_updates),
        )

    def _update_referees(self):
       ...

    def _update_coaches(self):
        ...

    def _update_lineup(self):
        for lineup_idx, lineup in enumerate(self.reader.lineup):
            team = self.game.home_team if lineup_idx == 0 else self.game.visitor_team
            for line_idx, line in lineup.items():
                ...

    @with_error_logging
    def _update_player_stats(self):
        for team_idx, player_stats in enumerate(self.reader.player_stats):
            team = self.game.home_team if team_idx == 0 else self.game.visitor_team
            for period, period_stats in player_stats.items():
                for row in period_stats:
                    ...

    def _update_team_stats(self):
        for team_idx, team_stats in enumerate(self.reader.team_stats):
            team = self.game.home_team if team_idx == 0 else self.game.visitor_team
            for period, period_stats in team_stats.items():
                ...

    def _update_goals(self):
        # Удалить голы, отмененные после видеопросмотров
        ...

    def _update_disallowed_goals(self):
        ...

    def _update_penalties(self):
        # Удалить штрафы, отмененные после видеопросмотров
        ...

    def _update_video_reviews(self):
        ...

    def _update_penalty_shots(self):
        ...

    def _update_shootouts(self):
        ...

    def _update_goalie_subs(self):
        ...