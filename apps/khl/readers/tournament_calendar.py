from .base import KhlReader


class TournamentCalendarReader(KhlReader):

    def __init__(self, tournament_id,  khl_domain='www.khl.ru'):
        super().__init__()
        # reader vars
        self.api_payload = f'values[tournament]={tournament_id}'
        self.source_page_url = f'https://{khl_domain}/calendar/'
        self.calendar_api_url = f'https://{khl_domain}/rest/calendar/list/'
        self.tournament_id = tournament_id
        # source data
        self.calendar_data=None
        # output data
        self._arenas=[]
        self._games=[]

    async def _run_ops(self):
        self.api_payload += f'&sessid={self.khl_sessid}'
        await self._fetch_api_data(self.calendar_api_url, 'calendar_data')

    @property
    def games(self):
        if not self._games:
            for week in self.calendar_data.get('GAMES', []):
                if not isinstance(week, dict):
                    continue
                self._games.extend([
                    game for day in week.values() if day is not None
                    for game in day if game['tnId'] == self.tournament_id
                ])
        return self._games

    @property
    def arenas(self):
        if not self._arenas:
            self._arenas = [
                {'id': int(arena_id), 'city': city}
                for arena_id, city in self.calendar_data.get('ARENAS', {}).items() if city
            ]
        return self._arenas
