import asyncio
import logging
from datetime import datetime

from apscheduler.triggers.cron import CronTrigger

from apps.khl.models import Team, SeasonTeam, Season, Tournament, Game
from apps.khl.processors.game_broadcast import GameBroadcastDataProcessor
from apps.khl.readers.game_broadcast import GameBroadcastReader
from apps.khl.readers.seasons import SeasonsReader
from apps.khl.readers.tournament_calendar import TournamentCalendarReader
from apps.khl.services import TournamentService, GameService, ArenaService
from core.db.service import DbService
from core.db.session import SessionLocal
from core.utils import singleton_task, task_info

logger = logging.getLogger()

@task_info("Обновление списка сезонов КХЛ")
async def fetch_khl_seasons():
    async with SessionLocal() as session:
        async with SeasonsReader() as sr:
            if sr.errors:
                return
            ssn_svc = DbService(session, Season)
            trn_svc = TournamentService(session)
            tm_svc = DbService(session, Team)
            ssn_tm_svc = DbService(session, SeasonTeam)
            updated_teams = []
            for season_data in sr.seasons[::-1]:
                season, _ = await ssn_svc.get_or_create(
                    year_start=season_data.get('start'), year_end=season_data.get('end')
                )
                for tournament_data in season_data.get('tournaments', []):
                    tournament, created = await trn_svc.get_or_create(
                        khl_id=tournament_data.get('id'),
                        defaults={'part': tournament_data.get('part'), 'season_id': season.id}
                    )
                    if tournament_data.get('current') and not tournament.current:
                        await trn_svc.set_current(tournament)
                for team_data in season_data.get('teams', []):
                    team_id = team_data.get('id')
                    db_action = f"{'get' if team_id in updated_teams else 'update'}_or_create"
                    updated_teams.append(team_id)
                    try:
                        await getattr(tm_svc, db_action)(
                                khl_id=team_data.get('id'),
                                defaults={'name': team_data.get('name'), 'image': team_data.get('logo')}
                            )
                        await ssn_tm_svc.get_or_create(
                                season_id=season.id, team_id=team_id,
                                defaults={'name': team_data.get('name'), 'image': team_data.get('logo')}
                            )
                    except Exception as e:
                        logger.error(e)

@singleton_task
@task_info('Получение календарей необработанных турниров')
async def fetch_calendars_for_empty_tournaments():
    async with SessionLocal() as session:
        trn_svc = TournamentService(session)
        await asyncio.gather(*[
            asyncio.create_task(fetch_calendar(et.khl_id))
            for et in await trn_svc.all(where=[~trn_svc.model.games.any()])
        ])


@singleton_task
@task_info("Обновление календаря турнира")
async def fetch_calendar(tournament: int | Tournament = None):
    async with SessionLocal.begin() as session:
        trn_svc = TournamentService(session)
        arn_svc = ArenaService(session)
        gm_svc = GameService(session)
        if tournament is None:
            tournament = await trn_svc.get_current()
        elif isinstance(tournament, int):
            tournament = await trn_svc.first(khl_id=tournament)
        if tournament:
            logger.warning(f'Обновление календаря турнира {tournament.khl_id}...')
            async with TournamentCalendarReader(tournament.khl_id) as tcr:
                if not tcr.errors:
                    await arn_svc.update_from_calendar(tcr.arenas)
                    await gm_svc.update_from_calendar(tcr.games)
                    logger.warning(f'Календарь турнира {tournament.khl_id} обновлен')
                else:
                    logger.error(f'Ошибка получения календаря турнира {tournament.khl_id}: {tcr.errors}')

@singleton_task
@task_info("Обработка трансляции игры")
async def fetch_broadcast(game: Game):
    async with SessionLocal.begin() as session:
        logger.warning(f'Обработка трансляции игры {game.khl_id}...')
        async with GameBroadcastReader(game.tournament.khl_id, game.khl_id) as gbr:
            if not gbr.errors:
                await GameBroadcastDataProcessor(session, gbr, game).update_db()
                logger.warning(f'Трансляция игры {game.khl_id} обработана')
            else:
                logger.warning(f'Ошибка обработки трансляции игры {game.khl_id}: {gbr.errors}')
            return gbr

tasks = [
    # {
    #     'func': fetch_khl_seasons,
    #     'trigger': CronTrigger(day_of_week=0),
    #     'next_run_time':datetime.now()
    # },
    # {
    #     'func': fetch_calendar,
    #     'trigger': CronTrigger(hour='*/12', minute=0),
    #     'next_run_time':datetime.now()
    # },
    # {
    #     'func': fetch_calendars_for_empty_tournaments,
    #     'trigger': CronTrigger(day_of_week=0),
    #     'next_run_time': datetime.now()
    # },
]
