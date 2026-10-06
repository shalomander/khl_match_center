from typing import List

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page
from starlette import status
from starlette.requests import Request

from apps.khl.models import Season
from core.db.service import DbService
from core.dependencies import DBDependency
from .schemas import SeasonResponse
from ..tournaments.schemas import TournamentResponse

router = APIRouter()


@router.get("/", name="Список сезонов")
async def get_seasons_list(request: Request, db: DBDependency) -> Page[SeasonResponse]:
    return await (DbService(db, Season).paginate(order_by='year_start DESC'))


@router.get("/{season_id}/", name="Один сезон")
async def get_season(request: Request, db: DBDependency, season_id: int) -> SeasonResponse:
    if not (season := await (DbService(db, Season).first(id=season_id))):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return season


@router.get("/{season_id}/tournaments", name="Список турниров сезона")
async def get_season_tournaments_list(request: Request, db: DBDependency, season_id: int) -> List[TournamentResponse]:
    if not (season := await (DbService(db, Season).first(id=season_id))):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return season.tournaments
