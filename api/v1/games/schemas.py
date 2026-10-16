from datetime import datetime

from pydantic import BaseModel


class Game(BaseModel):
    khl_id: int
    start_at: datetime
    home_team: GameTeam
    visitor_team: GameTeam
    arena: GameArena

class GameTeam(BaseModel):
    khl_id: int
    name: str

class GameArena(BaseModel):
    khl_id: int
    name: str|None
    city: str|None