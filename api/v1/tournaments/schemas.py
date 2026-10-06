from typing import Literal

from pydantic import BaseModel


class TournamentFilters(BaseModel):
    part: Literal['regular', 'playoff']|None = None
    season_id: int|None = None

class TournamentResponse(BaseModel):
    khl_id: int
    part: str

