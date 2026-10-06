from pydantic import BaseModel


class TeamResponse(BaseModel):
    khl_id: int
    name: str