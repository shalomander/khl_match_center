from datetime import datetime, timezone
from typing import Dict, Any

from pydantic import BaseModel, Field, model_validator


class CalendarGame(BaseModel):
    khl_id: int = Field(alias="id")
    arena_id: int|None = Field(alias="arenaid", exclude_if=lambda x: x==0)
    tournament_id: int = Field(alias="tnId")
    home_team_id: int = Field(alias="teama")
    visitor_team_id: int = Field(alias="teamb")
    start_at: datetime|None
    home_score: int|None = Field(default=None, alias="homeScore")
    visitor_score: int|None = Field(default=None, alias="visitorScore")
    ots: str
    is_over: bool

    @model_validator(mode='before')
    def update_input(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if 'date' in values and 'time_format' in values:
            dt_str = f'{values["date"]}T{values["time_format"]}:00+03:00'
            values['start_at'] = datetime.fromisoformat(dt_str).astimezone(timezone.utc).replace(tzinfo=None)
        values['is_over'] = values.get('approved', 0)==1
        return values

class BroadcastGameInfo(BaseModel):
    arena_id: int|None
    attendance: int|None
    home_score: int|None
    visitor_score: int|None
    ots: str|None
    is_over: bool = Field(default=False)
    broadcast_processed: bool = Field(default=False, alias="is_over")
    # После окончания игры трансляция не обновляется, broadcast_processed=is_over
