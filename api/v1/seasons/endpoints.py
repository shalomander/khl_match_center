from typing import List

from fastapi import APIRouter
from fastapi_pagination import Page

from core.dependencies import SeasonRepo
from core.utils import get_or_raise_404
from . import schemas
from ..tournaments import schemas as tournament_schemas

router = APIRouter()


@router.get("/", name="Список сезонов")
async def get_seasons_list(ssn_repo: SeasonRepo) -> Page[schemas.Season]:
    return await ssn_repo.paginate(order_by='year_start DESC')


@router.get("/{season_id}/", name="Один сезон")
async def get_season(ssn_repo: SeasonRepo, season_id: int) -> schemas.Season:
    return get_or_raise_404(await ssn_repo.first(id=season_id))


@router.get("/{season_id}/tournaments", name="Список турниров сезона")
async def get_season_tournaments(ssn_repo: SeasonRepo, season_id: int) -> List[tournament_schemas.Tournament]:
    season = get_or_raise_404(await ssn_repo.first(id=season_id))
    return season.tournaments
