import asyncio
import re
from contextlib import suppress
from typing import Coroutine

import aiohttp
from aiohttp import ClientResponse, ClientSession

BASE_TIMEOUT=5

class SourceFetchError(Exception):
    def __init__(self, response: ClientResponse):
        self.status = response.status
        self.content = response.content
        super().__init__(f"Source page content is not available: {self.status}")


class KhlReader:
    PLAYER_POSITIONS = {
        "в": "goalie",
        "з": "defenseman",
        "н": "forward"
    }
    CAPTAIN_MAP = {
        "а": "A",
        "к": "C"
    }
    COMMON_REGEXES = {
        'KHL_SESSID': ''
    }
    REGEXES = {}
    COMMON_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0'
    }
    API_HEADERS = {
        **COMMON_HEADERS,
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }

    def __init__(self):
        self.source_page_url: str = None
        self.session:ClientSession = None
        self.api_payload: str = ''
        self.khl_sessid=None
        self.errors = []
        self.request_timeout = aiohttp.ClientTimeout(total=BASE_TIMEOUT)

    async def __aenter__(self):
        async with aiohttp.ClientSession(headers=self.COMMON_HEADERS, timeout=self.request_timeout) as self.session:
            try:
                await self._asyncio_gather(
                    self._compile_regexes(),
                    self._fetch_page_html()
                )
                await self._run_ops()
            except Exception as e:
                self.errors.append(repr(e))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ...

    async def _fetch_page_html(self) -> None:
        if self.source_page_url:
            async with self.session.get(self.source_page_url) as response:
                if response.status != 200:
                    raise SourceFetchError(response)
                with suppress(Exception):
                    content = await response.text()
                    if re_obj := re.search(r'"bitrix_sessid":"([a-z0-9]+)"', content):
                        self.khl_sessid = re_obj.group(1)

    async def _fetch_api_data(self, api_url: str, attr: str):
        async with self.session.post(api_url, headers=self.API_HEADERS, data=self.api_payload) as response:
            if response.status == 200 and (api_data := await response.json()):
                if api_data.get('status') == 'success':
                    setattr(self, attr, api_data.get('data', {}))
                else:
                    self.errors.extend([
                        f'Ошибка доступа к апи КХЛ[{api_url}]: {str(e)}' for e in api_data.get('errors', [])
                    ])

    async def _compile_regexes(self) -> None:
        for k, v in {**self.COMMON_REGEXES, **self.REGEXES}.items():
            setattr(self, f'{k}_REGEX', re.compile(v))


    async def _run_ops(self) -> None:
        ...

    async def _asyncio_gather(self, *coros: Coroutine):
        if hasattr(asyncio, 'TaskGroup'):
            async with asyncio.TaskGroup() as group:
               for coro in coros:
                    group.create_task(coro)
        else:
            await asyncio.gather(*coros)

    def _int(self, s: str, default: int = 0) -> int:
        try:
            return int(s)
        except:
            return default

    def _float(self, s: str, default: float = 0.0) -> float:
        try:
            return float(s)
        except:
            return default

    def _int_time(self, s: str):
        with suppress(Exception):
            minutes, seconds, *_ = s.split(':')
            return int(minutes) * 60 + int(seconds)
        return None