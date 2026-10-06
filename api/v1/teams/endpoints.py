from fastapi import APIRouter
from fastapi_pagination import Page
from starlette.requests import Request

from apps.khl import models
from core.db.service import DbService
from core.dependencies import DBDependency
from .schemas import TeamResponse

router = APIRouter()

@router.get("/", name="Список команд")
async def get_teams_list(request: Request, db: DBDependency) -> Page[TeamResponse]:
    return await (DbService(db, models.Team).paginate())
