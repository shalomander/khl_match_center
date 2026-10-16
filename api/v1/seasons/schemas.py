from typing import List

from pydantic import BaseModel, Field


class Season(BaseModel):
    id: int
    year_start: int
    year_end: int
    tournaments: List[SeasonTournament]
    teams: List[SeasonTeam]

class SeasonTournament(BaseModel):
    khl_id: int
    part: str

class SeasonTeam(BaseModel):
    khl_id: int = Field(alias="team_id")
    name: str