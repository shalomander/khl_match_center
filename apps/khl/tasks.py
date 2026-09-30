import asyncio
import logging

from apscheduler.triggers.cron import CronTrigger

from apps.khl.models import Tournament, Team, SeasonTeam, Season
from apps.khl.readers.seasons import SeasonsReader
from apps.khl.services import TournamentService
from core.db.service import DbService
from core.db.session import SessionLocal

logger = logging.getLogger()


async def fetch_khl_seasons():
    async with SessionLocal() as session:
        async with SeasonsReader() as sr:
            season_svc = DbService(session, Season)
            tournament_svc = TournamentService(session)
            team_svc = DbService(session, Team)
            season_team_svc = DbService(session, SeasonTeam)
            updated_teams = []
            for season_data in sr.seasons[::-1]:
                season, _ = await season_svc.get_or_create(
                    year_start=season_data.get('start'),
                    year_end=season_data.get('end')
                )
                for tournament_data in season_data.get('tournaments', []):
                    tournament, _ = await tournament_svc.get_or_create(
                        khl_id=tournament_data.get('id'),
                        defaults={'part': tournament_data.get('part'), 'season_id': season.id}
                    )
                    if tournament_data.get('current') and not tournament.current:
                        await tournament_svc.set_current(tournament)
                for team_data in season_data.get('teams', []):
                    team_id = team_data.get('id')
                    db_action = f"{'get' if team_id in updated_teams else 'update'}_or_create"
                    updated_teams.append(team_id)
                    await asyncio.gather(
                        asyncio.create_task(getattr(team_svc, db_action)(
                            khl_id=team_data.get('id'),
                            defaults={'name': team_data.get('name'), 'image': team_data.get('logo')}
                        )),
                        asyncio.create_task(season_team_svc.get_or_create(
                            season_id=season.id,
                            team_id=team_id,
                            defaults={'name': team_data.get('name'), 'image': team_data.get('logo')}
                        )))


tasks = [
    # {'func': fetch_khl_seasons, 'trigger': CronTrigger(second='*/10')}
]
