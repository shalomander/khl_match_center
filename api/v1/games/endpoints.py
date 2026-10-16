from fastapi import APIRouter
from fastapi_pagination import Page

from apps.khl_data.tasks import fetch_broadcast
from core.dependencies import GameRepo
from core.utils import get_or_raise_404
from . import schemas

router = APIRouter()


@router.get("/", name="Список игр")
async def get_games_list(gm_repo: GameRepo) -> Page[schemas.Game]:
    return await gm_repo.paginate(order_by='khl_id DESC')


@router.get("/{khl_id}/", name="Одна игра")
async def get_game(gm_repo: GameRepo, khl_id: int) -> schemas.Game:
    return get_or_raise_404(await gm_repo.first(khl_id=khl_id))


@router.get("/{khl_id}/review/", name="Обзор игры")
async def get_game_review(gm_repo: GameRepo, khl_id: int):
    game = get_or_raise_404(await gm_repo.first(khl_id=khl_id))
    if True:  # TODO: условие, при котором требуется принудительный запуск парсера
        gbr = await fetch_broadcast(game)
        return gbr.dump()
