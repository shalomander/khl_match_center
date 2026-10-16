from typing import Annotated

from fastapi import APIRouter, Query
from fastapi_pagination import Page

from apps.khl_data.tasks import fetch_calendar
from core.dependencies import TournamentRepo, GameRepo
from core.utils import get_or_raise_404
from . import schemas
from ..games import schemas as game_schemas

router = APIRouter()


@router.get("/", name="Список турниров")
async def get_tournaments_list(
        trn_repo: TournamentRepo,
        filters: Annotated[schemas.TournamentFilters, Query()]
) -> Page[schemas.Tournament]:
    return await trn_repo.paginate(filter_by=filters.model_dump(exclude_unset=True))


@router.get("/{khl_id}/", name="Один турнир")
async def get_tournament(trn_repo: TournamentRepo, khl_id: int) -> schemas.Tournament:
    return get_or_raise_404(await trn_repo.first(khl_id=khl_id))


@router.get("/{khl_id}/games/", name="Список игр турнира")
async def get_tournament_games(trn_repo: TournamentRepo, gm_repo: GameRepo, khl_id: int) -> Page[game_schemas.Game]:
    get_or_raise_404(await trn_repo.first(khl_id=khl_id))
    if not await gm_repo.exists(tournament_id=khl_id):
        await fetch_calendar(khl_id)
    return await gm_repo.paginate(tournament_id=khl_id, order_by='start_at asc')
