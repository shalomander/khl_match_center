from contextlib import suppress

from .base import KhlReader


class SeasonsReader(KhlReader):
    PART_MAP = {
        'Регулярный чемпионат': 'regular',
        'Плей-офф': 'playoff'
    }

    def __init__(self, khl_domain='www.khl.ru'):
        super().__init__()
        # reader vars
        self.api_payload = None
        self.source_page_url = f'https://{khl_domain}/calendar/'
        self.filters_api_url = f'https://{khl_domain}/rest/filters/calendar/'
        self._current_tournament = None
        # source data
        self.filters_data = None
        self.season_filter_data = None
        # output data
        self._seasons = {}

    async def _run_ops(self):
        self.api_payload = f'sessid={self.khl_sessid}'
        await self._fetch_api_data(self.filters_api_url, 'filters_data')
        await self._extract_data()

    async def _extract_data(self):
        filters = self.filters_data.get('LIST', {})
        for t in filters.get('tournament', {}).get('VALUE', []):
            if 'active' in t:
                self._current_tournament = t['i']
        extract_season_coros = []
        for season in reversed(filters.get('season', {}).get('VALUE', [])):
            with suppress(Exception):
                start, end = season.get('name', '-').split('-')
                self._seasons[season.get('i')] = {'start': int(start), 'end': int(end)}
                extract_season_coros.append(self._extract_season(season.get('i')))
        await self._asyncio_gather(*extract_season_coros)

    async def _extract_season(self, season):
        payload = f'{self.api_payload}&values[season]={season}'
        async with self._session.post(self.filters_api_url, headers=self.API_HEADERS, data=payload) as resp:
            if resp.status == 200 and (api_data := await resp.json()) and api_data.get('status') == 'success':
                tournaments = api_data.get('data', {}).get('LIST', {}).get('tournament', {}).get('VALUE', [])
                teams = api_data.get('data', {}).get('LIST', {}).get('clubs', {}).get('VALUE', [])
                with suppress(Exception):
                    self._seasons[season]['tournaments'] = [
                        {
                            'id': int(t['i']),
                            'part': self.PART_MAP[t['name']],
                            'current': self._current_tournament == t['i']
                        } for t in tournaments if t['name'] in self.PART_MAP
                    ]
                    self._seasons[season]['teams'] = [
                        {'id': int(t['i']), 'name': t['name'], 'logo': f"https:{t['logo']}"}
                        for t in teams if t.get('i', '').isdigit()
                    ]

    @property
    def seasons(self) -> list:
        return list(self._seasons.values())

