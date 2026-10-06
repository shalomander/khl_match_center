from typing import Annotated

from fastapi import APIRouter, Query, HTTPException
from fastapi_pagination import Page
from starlette import status
from starlette.requests import Request

from apps.khl.services import TournamentService, GameService
from apps.khl.tasks import fetch_calendar
from core.dependencies import DBDependency
from .schemas import TournamentResponse, TournamentFilters
from ..games.schemas import GameResponse

router = APIRouter()


@router.get("/", name="Список турниров")
async def get_tournaments_list(
        request: Request,
        db: DBDependency,
        filters: Annotated[TournamentFilters, Query()]
) -> Page[TournamentResponse]:
    return await (TournamentService(db).paginate(filter_by=filters.model_dump(exclude_unset=True)))


@router.get("/{khl_id}/", name="Один турнир")
async def get_tournament(request: Request, db: DBDependency, khl_id: int) -> TournamentResponse:
    if not (tournament := await (TournamentService(db).first(khl_id=khl_id))):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return tournament


@router.get("/{khl_id}/games/", name="Список игр турнира")
async def get_tournament_games(request: Request, db: DBDependency, khl_id: int) -> Page[GameResponse]:
    if not await (TournamentService(db).exists(khl_id=khl_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if not await (GameService(db).exists(tournament_id=khl_id)):
        await fetch_calendar(khl_id)
    return await (GameService(db).paginate(tournament_id=khl_id, order_by='start_at asc'))
