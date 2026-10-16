import asyncio
import logging
from datetime import datetime

from apscheduler.triggers.cron import CronTrigger

from apps.games.models import Game
from apps.khl_data.processors.game_broadcast import GameBroadcastDataProcessor
from apps.khl_data.processors.tournament_calendar import TournamentCalendarDataProcessor
from apps.khl_data.readers.game_broadcast import GameBroadcastReader
from apps.khl_data.readers.seasons import SeasonsReader
from apps.khl_data.readers.tournament_calendar import TournamentCalendarReader
from apps.teams.models import Team
from apps.tournaments.models import Season, SeasonTeam, Tournament
from apps.tournaments.repositories import TournamentRepository
from core.db.session import SessionLocal
from core.utils import singleton_task, task_info

logger = logging.getLogger()

@task_info("Обновление списка сезонов КХЛ")
async def fetch_khl_seasons():
    async with SessionLocal() as session:
        async with SeasonsReader() as sr:
            if sr.errors:
                return
            ssn_repo = DbService(session, Season)
            trn_repo = TournamentRepository(session)
            tm_repo = DbService(session, Team)
            ssn_tm_repo = DbService(session, SeasonTeam)
            updated_teams = []
            for season_data in sr.seasons[::-1]:
                season, _ = await ssn_repo.get_or_create(
                    year_start=season_data.get('start'), year_end=season_data.get('end')
                )
                for tournament_data in season_data.get('tournaments', []):
                    tournament, created = await trn_repo.get_or_create(
                        khl_id=tournament_data.get('id'),
                        defaults={'part': tournament_data.get('part'), 'season_id': season.id}
                    )
                    if tournament_data.get('current') and not tournament.current:
                        await trn_repo.set_current(tournament)
                for team_data in season_data.get('teams', []):
                    team_id = team_data.get('id')
                    db_action = f"{'get' if team_id in updated_teams else 'update'}_or_create"
                    updated_teams.append(team_id)
                    try:
                        await getattr(tm_repo, db_action)(
                                khl_id=team_data.get('id'),
                                defaults={'name': team_data.get('name'), 'image': team_data.get('logo')}
                            )
                        await ssn_tm_repo.get_or_create(
                                season_id=season.id, team_id=team_id,
                                defaults={'name': team_data.get('name'), 'image': team_data.get('logo')}
                            )
                    except Exception as e:
                        logger.error(e)

@singleton_task
@task_info('Получение календарей необработанных турниров')
async def fetch_calendars_for_empty_tournaments():
    async with SessionLocal() as session:
        trn_repo = TournamentRepository(session)
        await asyncio.gather(*[
            asyncio.create_task(fetch_calendar(et.khl_id))
            for et in await trn_repo.all(where=[~trn_repo.model.games.any()])
        ])


@singleton_task
@task_info(f"Обновление календаря турнира")
async def fetch_calendar(tournament: int | Tournament = None):
    async with SessionLocal.begin() as session:
        trn_repo = TournamentRepository(session)
        if not isinstance(tournament, trn_repo.model):
            tournament = await trn_repo.get_one_or_current(tournament)
        if tournament:
            logger.warning(f'Обновление календаря турнира {tournament.khl_id}...')
            async with TournamentCalendarReader(tournament.khl_id) as tcr:
                await TournamentCalendarDataProcessor(session, tcr, tournament).update_db()


@singleton_task
@task_info("Обработка трансляции игры")
async def fetch_broadcast(game: Game):
    async with SessionLocal.begin() as session:
        logger.warning(f'Обработка трансляции игры {game.khl_id}...')
        async with GameBroadcastReader(game.tournament.khl_id, game.khl_id) as gbr:
            await GameBroadcastDataProcessor(session, gbr, game).update_db()
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
