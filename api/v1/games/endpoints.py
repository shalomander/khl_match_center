from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page
from starlette import status
from starlette.requests import Request

from apps.khl.services import GameService
from apps.khl.tasks import fetch_broadcast
from core.dependencies import DBDependency
from .schemas import GameResponse

router = APIRouter()

@router.get("/", name="Список игр")
async def get_games_list(request: Request, db: DBDependency) -> Page[GameResponse]:
    return await (GameService(db).paginate())


@router.get("/{khl_id}/", name="Одна игра")
async def get_game(request: Request, db: DBDependency, khl_id:int) -> GameResponse:
    if not (game:= await GameService(db).first(khl_id=khl_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return game

@router.get("/{khl_id}/review/", name="Обзор игры")
async def get_game(request: Request, db: DBDependency, khl_id:int):
    if not (game:= await GameService(db).first(khl_id=khl_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    gbr = await fetch_broadcast(game)
    return gbr.dump()
