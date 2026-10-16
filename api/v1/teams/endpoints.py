from fastapi import APIRouter
from fastapi_pagination import Page

from core.dependencies import TeamRepo
from . import schemas

router = APIRouter()


@router.get("/", name="Список команд")
async def get_teams_list(tm_repo: TeamRepo) -> Page[schemas.Team]:
    return await tm_repo.paginate(order_by='name ASC')
