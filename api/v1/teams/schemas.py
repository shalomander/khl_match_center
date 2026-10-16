from pydantic import BaseModel


class Team(BaseModel):
    khl_id: int
    name: str